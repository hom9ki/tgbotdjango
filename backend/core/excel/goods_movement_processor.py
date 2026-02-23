from .base_exel_processor import FileProcessor
from .goods_movement_report import GoodsMovementReport


class GoodsMovementProcessor(FileProcessor):
    def process(self, file_bytes: bytes, file_name: str):
        try:
            editor = GoodsMovementReport(file_bytes, file_name)
            processed_stream = editor.get_stream
            new_filename = editor.get_filename

            return processed_stream, {
                'filename': new_filename,
                'type': 'goods_movement',
                'success': True,
                'message': f'Файл {file_name} перемещения товаров успешно обработан!'
            }
        except Exception as e:
            return file_bytes, {
                'filename': file_name,
                'type': 'goods_movement',
                'success': False,
                'error': str(e)
            }
