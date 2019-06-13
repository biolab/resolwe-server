from resolwe.process import *


class WordCountBasic(Process):
    name = 'Word Count'
    slug = 'wc-basic'
    process_type = 'data:wc'
    version = '1.0.0'

    class Input:
        doc = FileField('Document')

    class Output:
        words = IntegerField('Number of words')

    def run(self, inputs, outputs):
        with open(inputs.doc.file_temp) as fp:
            words = len(fp.read().split())

        outputs.words = words


class UploadDocument(Process):
    name = 'Upload Document'
    slug = 'upload-doc'
    process_type = 'data:doc'
    version = '1.0.0'

    class Input:
        src = FileField('Document')

    class Output:
        dst = FileField('Document')

    def run(self, inputs, outputs):
        outputs.dst = inputs.src.import_file()


class WordCount(Process):
    name = 'Word Count'
    slug = 'wc'
    process_type = 'data:stat:wc'
    version = '1.0.0'

    class Input:
        doc = DataField('doc', 'Document')

    class Output:
        words = IntegerField('Number of words')

    def run(self, inputs, outputs):
        with open(inputs.doc.dst.path) as fp:
            outputs.words = len(fp.read().split())


class LineCount(Process):
    name = 'Line Count'
    slug = 'ln'
    process_type = 'data:stat:ln'
    version = '1.0.0'

    class Input:
        doc = DataField('doc', 'Document')

    class Output:
        lines = IntegerField('Number of lines')

    def run(self, inputs, outputs):
        with open(inputs.doc.dst.path) as fp:
            outputs.lines = len(fp.readlines())
