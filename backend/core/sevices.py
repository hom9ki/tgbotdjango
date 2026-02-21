import io

from django.core.files.uploadedfile import InMemoryUploadedFile


def create_in_memory_uploaded_file(file):
    file_bytes = file.read()
    virtual_file = io.BytesIO(file_bytes)
    file.seek(0)
    virtual_file.seek(0)
    return InMemoryUploadedFile(
        file=virtual_file,
        field_name='file',
        name=get_file_name(file),
        content_type=file.content_type,
        size=len(file_bytes),
        charset=None
    ), file_bytes


def get_file_information(file, request, doc_type_default, contxt=''):
    title = f'{request.data.get('title', '')}'.rstrip()
    if title != '':
        title = file.name.split('.')[0]

    return {
        'file': file,
        'title': f'{title} {contxt}'.rstrip(),
        'description': request.data.get('description', ''),
        'doc_type': request.data.get('doc_type', doc_type_default),
        'should_compress': request.data.get('should_compress', False)
    }


def get_file_name(file):
    return file.name
