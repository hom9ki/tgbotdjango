from .base_exel_processor import FileProcessor
from .multiplicity_report import miltiplicity_processing_excel


class MultiplicityProcessor(FileProcessor):
    def process(self, file_bytes, file_name):
        try:
            multiplicity_bytes = miltiplicity_processing_excel(file_bytes)
            base_name = file_name.split('.')[0]
            extension = file_name.split('.')[-1]
            new_filename = f'{base_name}_кратность.{extension}'

            return multiplicity_bytes, {
                'filename': new_filename,
                'type': 'multiplicity',
                'success': True,
                'message': f'Кратность успешно добавлена в файл {new_filename}!'
            }
        except Exception as e:

            return file_bytes, {
                'filename': file_name,
                'type': 'multiplicity',
                'success': False,
                'error': str(e)}
