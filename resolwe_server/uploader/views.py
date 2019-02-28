"""Django views."""
import base64
from datetime import datetime
import json
import logging
import os
import re
import mimetypes

from wsgiref.util import FileWrapper

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseServerError, Http404
from django.shortcuts import redirect

from ..base.views import authorization

from . utils import uploader, get_upload_id, _remove_file

# Exports.
__all__ = (
    'file_upload',
    'file_download',
)


logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


def upload_lock(upload_function):
    """Prevent upload of the same file in multiple threads."""
    def new_upload(request):
        """Upload details."""
        session_id = request.META.get('HTTP_SESSION_ID', None)
        file_uid = request.META.get('HTTP_X_FILE_UID', None)

        if session_id is None or file_uid is None:
            return HttpResponseBadRequest("Session-Id and X-File-Uid must be given in header")

        upload_id = get_upload_id(session_id, file_uid, settings.SECRET_KEY)

        filetemp = os.path.join(settings.FLOW_EXECUTOR['UPLOAD_DIR'], upload_id)
        lock_fn = '{}.lock'.format(filetemp)
        lock_fd = None
        try:
            lock_fd = os.open(lock_fn, os.O_CREAT | os.O_EXCL | os.O_RDWR)
        except OSError as ex:
            if ex.errno != os.errno.EEXIST:
                raise

            return HttpResponseBadRequest("Uploading the same file in two threads")
        finally:
            if lock_fd is not None:
                os.close(lock_fd)

        try:
            return upload_function(request)
        finally:
            _remove_file(lock_fn)

    return new_upload


@login_required
@upload_lock
def file_upload(request):
    """Chunked upload."""
    def response_func(status, data='', content_type='text/plain'):
        """Format response."""
        return HttpResponse(content=data, content_type=content_type, status=status)

    request_method = request.method
    session_id = request.META.get('HTTP_SESSION_ID', None)
    file_uid = request.META.get('HTTP_X_FILE_UID', None)
    secret_key = settings.SECRET_KEY
    upload_dir = settings.FLOW_EXECUTOR['UPLOAD_DIR']

    post_data = {}
    if request_method == 'POST':
        try:
            post_data = {
                '_totalSize': request.POST['_totalSize'],
                '_chunkSize': request.POST['_chunkSize'],
                '_chunkNumber': request.POST['_chunkNumber'],
                '_currentChunkSize': request.POST['_currentChunkSize'],
                'file': request.FILES['file'],
                'filename': request.FILES['file'].name,
            }
        except (ValueError, KeyError):
            msg = "Malformed chunk metadata"
            logger.warning(msg)
            return response_func(400, msg)

    return uploader(request_method, post_data, session_id, file_uid, secret_key, upload_dir, response_func)


def file_download(request, data_id, uri, token=None, gzip_header=False):
    """Download data.

    Required for download through Django's lightweight development Web server.
    Overridden by Nginx.

    """
    if token is not None:
        # Copy the token to the authentication header if it was send in the URL.
        b64_credentials = base64.b64encode(b'token:' + token.encode('utf-8'))
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + b64_credentials.decode('utf-8')
        request.META['PATH_INFO'] = '/data/{}/{}'.format(data_id, uri)

    # There are some differences between Nginx and Django handling of the request.
    request.META['HTTP_REQUEST_URI'] = request.META['PATH_INFO']

    auth_response = authorization(request)

    if auth_response.status_code in [400, 403]:
        return auth_response
    elif auth_response.status_code != 200:
        return HttpResponseServerError()

    def extract_range(range_, total_len):
        """Return byte ragne bounds."""
        bytes_ = re.search(r"^bytes=(\d*)-(\d*)$", range_).groups()
        if bytes_[0]:
            lower_bound = int(bytes_[0])
            if bytes_[1]:
                upper_bound = min(int(bytes_[1]), total_len - 1)
            else:
                upper_bound = total_len - 1
            return lower_bound, upper_bound, upper_bound - lower_bound + 1
        else:
            return None

    uri = uri.lstrip('/')  # prevent accessing parent directories

    filename = os.path.join(settings.FLOW_EXECUTOR['DATA_DIR'], data_id, uri)
    if not os.path.exists(filename):
        raise Http404()

    if os.path.isdir(filename):
        if uri != '' and not uri.endswith('/'):
            return redirect(uri + '/')

        files, dirs = [], []
        for fn in os.listdir(filename):
            file_path = os.path.join(filename, fn)
            is_file = os.path.isfile(file_path)

            stat = os.stat(file_path)
            modified = datetime.utcfromtimestamp(stat.st_mtime)

            stat_obj = {
                'name': fn,
                'type': "file" if is_file else "directory",
                'mtime': modified.strftime("%a, %d %b %Y %H:%M:%S GMT"),
            }

            if is_file:
                stat_obj['size'] = stat.st_size
                files.append(stat_obj)
            else:
                dirs.append(stat_obj)

        return HttpResponse(json.dumps(dirs + files), content_type="application/json")

    if gzip_header:
        # Check by magic number if file is really gzipped
        with open(filename) as f:
            gzip_header = f.read(3).startswith('\x1f\x8b\x08')

    total_len = os.path.getsize(filename)

    content_type, charset = mimetypes.guess_type(filename)

    response_kwargs = {
        'content_type': content_type,
        'charset': charset,
    }

    if 'HTTP_RANGE' in request.META:
        fhandle = open(filename, 'rb')
        range_params = extract_range(request.META['HTTP_RANGE'], total_len)
        if range_params is None:
            resp_len = total_len
        else:
            resp_len = range_params[2]
            fhandle.seek(range_params[0])

        wrapper = FileWrapper(fhandle)
        response = HttpResponse(wrapper, status=206, **response_kwargs)
        response['Content-Range'] = 'bytes %d-%d/%d' % (range_params[0], range_params[1], total_len)
        response['Accept-Ranges'] = 'bytes'
    else:
        resp_len = total_len
        wrapper = FileWrapper(open(filename, 'rb'))
        response = HttpResponse(wrapper, status=200, **response_kwargs)

    if gzip_header:
        response['Content-Encoding'] = 'gzip'

    if request.GET.get('force_download', None) == '1':
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(os.path.basename(filename))

    response['Content-Description'] = 'File Transfer'
    response['Content-Length'] = resp_len
    return response
