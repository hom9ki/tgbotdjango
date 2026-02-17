from .base_exel_processor import FileProcessor
from .price_list_edit import PriceListEdit


class PriceListProcessor(FileProcessor):
    def process(self, file_bytes, file_name):
        try:
            editor = PriceListEdit(file_bytes, file_name)
            processed_stream = editor.get_stream
            new_filename = editor.get_file_name

            return processed_stream, {
                'filename': new_filename,
                'type': 'price_list',
                'success': True,
                'message': f'Прайс-лист {file_name} успешно обработан!'
            }
        except Exception as e:

            return file_bytes, {
                'filename': file_name,
                'type': 'price_list',
                'success': False,
                'error': str(e)}
