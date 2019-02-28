"""User configuration."""
import re

from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.models import AnonymousUser, Group
from django.db.models import Q
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from resolwe.flow.models import Data

from rest_framework import serializers, viewsets, mixins, status, permissions
from rest_framework.decorators import detail_route, list_route
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework_filters.backends import DjangoFilterBackend

from ..filters import GroupFilter, UserFilter

# Exports.
__all__ = (
    'authorization',
    'UserViewSet',
    'GroupViewSet',
)


class IsStaffOrTargetUser(permissions.BasePermission):
    """Permission class for user endpoint."""

    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj == request.user


class IsSuperuserOrReadOnly(permissions.BasePermission):
    """Permission class for group endpoint."""

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS or (request.user and request.user.is_superuser)


class UserSerializer(serializers.ModelSerializer):
    """Serializer for :class:`User` objects."""

    class Meta:
        """Serializer configuration."""

        model = get_user_model()
        fields = ('id', 'first_name', 'last_name', 'username', 'password', 'email',
                  'date_joined', 'last_login')
        extra_kwargs = {'password': {'write_only': True}}


class GroupSerializer(serializers.ModelSerializer):
    """Serializer for :class:`Group` objects."""

    # NOTE: All groups can be seen by all authenticated users. So we
    #       don't want to reveal anything more than primary keys of
    #       users in groups.
    users = serializers.PrimaryKeyRelatedField(source='user_set', read_only=True, many=True)

    class Meta:
        """Serializer configuration."""

        model = Group
        fields = ('id', 'name', 'users')


class ChangePasswordSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """Serializer for changing the user password."""

    existing_password = serializers.CharField()
    new_password = serializers.CharField()


class ActivationSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """Serializer for user account activation."""

    token = serializers.CharField()


class PasswordResetRequestSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """Serializer for requesting a password reset."""

    username = serializers.CharField()
    community = serializers.CharField(required=False)


class PasswordResetSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """Serializer for password reset."""

    token = serializers.CharField()
    password = serializers.CharField()


class UserViewSet(mixins.ListModelMixin,
                  mixins.CreateModelMixin,
                  mixins.UpdateModelMixin,
                  viewsets.GenericViewSet):
    """API view for :class:`User` objects."""

    serializer_class = UserSerializer
    permission_classes = (IsStaffOrTargetUser,)
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filter_class = UserFilter

    def get_queryset(self):
        """Return query sets."""
        user = self.request.user
        user_model = get_user_model()

        # Only return information for the currently authenticated user if configured.
        if self.request.query_params.get('current_only', False):
            if user.is_authenticated:
                return user_model.objects.filter(pk=user.pk).select_related('profile')
            else:
                return user_model.objects.none()

        if user.is_superuser:
            return user_model.objects.all().select_related('profile')
        elif user.is_authenticated:
            return user_model.objects.filter(
                Q(groups__in=user.groups.all()) | Q(pk=user.pk)
            ).distinct('id').select_related('profile')
        else:
            return user_model.objects.none()

    @list_route(methods=['post'])
    def request_password_reset(self, request):
        """Request user password reset."""
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            user_model = get_user_model()
            try:
                user = user_model.objects.get(
                    Q(username=serializer.data['username']) | Q(email=serializer.data['username'])
                )
            except (user_model.DoesNotExist, user_model.MultipleObjectsReturned):
                return Response({'error': "User does not exist."},
                                status=status.HTTP_404_NOT_FOUND)

            send_reset_email(user, community=serializer.data.get('community', None))
            return Response({})
        else:
            return Response({'error': "Malformed password reset request."},
                            status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=['post'])
    def password_reset(self, request):
        """Reset user password."""
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            try:
                reset_password(
                    serializer.data['token'],
                    serializer.data['password'],
                )
                return Response({})
            except ValueError:
                return Response({'error': "Bad password reset token."},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': "Malformed password reset request."},
                            status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=['post'])
    def activate_account(self, request):
        """Activate user account."""
        serializer = ActivationSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = activate_account(serializer.data['token'])
                return Response({'username': user.username})
            except ValueError:
                return Response({'error': "Bad activation token."},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': "Malformed activation request."},
                            status=status.HTTP_400_BAD_REQUEST)

    @detail_route(methods=['post'])
    def change_password(self, request, pk=None):
        """Change user password."""
        user = self.get_object()
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            if not user.check_password(serializer.data['existing_password']):
                return Response({'error': "Incorrect password."},
                                status=status.HTTP_400_BAD_REQUEST)

            user.set_password(serializer.data['new_password'])
            user.save()
            update_session_auth_hash(request, user)
            return Response({})
        else:
            return Response({'error': "Malformed password."},
                            status=status.HTTP_400_BAD_REQUEST)


class GroupViewSet(mixins.ListModelMixin,
                   mixins.CreateModelMixin,
                   mixins.UpdateModelMixin,
                   viewsets.GenericViewSet):
    """API view for :class:`Group` objects."""

    serializer_class = GroupSerializer
    permission_classes = (IsSuperuserOrReadOnly,)
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filter_class = GroupFilter

    def get_queryset(self):
        """Return query sets."""
        user = self.request.user

        if user.is_superuser:
            return Group.objects.all()
        elif user.is_authenticated:
            return user.groups.all()
        else:
            return Group.objects.none()

    @detail_route(methods=['post'])
    def add_users(self, request, pk=None):
        """Endpoint for adding users to group."""
        group = self.get_object()

        users = request.data.get('user_ids')
        if not isinstance(users, list):
            users = [users]

        group.user_set.add(*users)

        return Response()

    @detail_route(methods=['post'])
    def remove_users(self, request, pk=None):
        """Endpoint for removing users from group."""
        group = self.get_object()

        users = request.data.get('user_ids')
        if not isinstance(users, list):
            users = [users]

        group.user_set.remove(*users)

        return Response()


@csrf_exempt  # TODO: add token to request
def authorization(request):
    """Check if user has authorization to access requested file.

    This function is used by nginx's ngx_http_auth_request_module
    module and follows it's specifications:

    http://nginx.org/en/docs/http/ngx_http_auth_request_module.html

    If the subrequest returns a 2xx response code, the access is
    allowed. If it returns 401 or 403, the access is denied with the
    corresponding error code. Any other response code returned by the
    subrequest is considered an error.

    """
    if 'HTTP_REQUEST_URI' not in request.META:
        return HttpResponse(status=403)

    uri = request.META['HTTP_REQUEST_URI']

    if re.match('/upload/$', uri):
        if not request.user.is_authenticated:
            return HttpResponse(status=403)
        return HttpResponse(status=200)

    uri_regex = re.match(r'/(data|datagzip)/(?P<data_id>\d+)/', uri)
    if uri_regex:
        data_id = uri_regex.group('data_id')

        try:
            data = Data.objects.get(pk=data_id)
        except Data.DoesNotExist:
            return HttpResponse(status=403)

        # Session authentication.
        pub_user = AnonymousUser()
        if pub_user.has_perm('view_data', data) and pub_user.has_perm('download_data', data):
            return HttpResponse(status=200)

        if (request.user.is_authenticated and
                request.user.has_perm('view_data', data) and
                request.user.has_perm('download_data', data)):
            return HttpResponse(status=200)

    return HttpResponse(status=403)
