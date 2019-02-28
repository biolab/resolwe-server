from resolwe import process
from resolwe.process import FileField, Cmd


class UploadFile(process.Process):
    """ Process description. """

    slug = 'file_upload'
    name = 'File upload'
    category = 'upload'
    version = '0.0.1'
    process_type = 'data:python'
    data_name = '{{ input_file.file|default("?") }}'
    requirements = {
        'expression-engine': 'jinja',
        'executor': {'docker': {'image': 'resolwe/base:ubuntu-18.04'}},
    }

    def update_descriptor(self, **kwargs):
        pass

    class Input:
        input_file = FileField(label='Input file', required=True)

    class Output:
        output_file = FileField(label='Output file')

    def run(self, inputs, outputs):
        Cmd['mv'][inputs.input_file.file_temp, inputs.input_file.path]()
        outputs.output_file = inputs.input_file
