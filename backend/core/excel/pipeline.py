from .base_exel_processor import FileProcessor


class ProcessingPipeline:
    def __init__(self, file_processor: FileProcessor):
        self.file_processor = file_processor

    def run(self, file_bytes: bytes, file_name: str) -> tuple:

        current_bytes = file_bytes
        current_filename = file_name

        processed_bytes, meta = self.file_processor.process(current_bytes, current_filename)

        if meta.get('success'):
            current_bytes = processed_bytes
            if meta.get('filename'):
                current_filename = meta.get('filename')

        return current_bytes, meta
