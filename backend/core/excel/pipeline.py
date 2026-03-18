from typing import Dict, Union

from .base_exel_processor import FileProcessor
from .base_excel_processor_V2 import ExcelProcessor


class ProcessingPipeline:
    # def __init__(self, file_processor: FileProcessor):
    #     self.file_processor = file_processor
    def __init__(self, desc_processor: Dict[str, Union[ExcelProcessor, str]]):
        self.file_processor = desc_processor.get('processor')
        self.type_report = desc_processor.get('type_processor')

    def run(self, file_bytes: bytes, file_name: str) -> tuple:
        current_bytes = file_bytes
        current_filename = file_name

        processed_bytes, meta = self.file_processor.process(current_bytes, current_filename, self.type_report)

        if meta.get('success'):
            current_bytes = processed_bytes

        return current_bytes, meta
