import unittest
from pathlib import Path
from ..registry import get_processor
from ..pipeline import ProcessingPipeline
from ..goods_movement_report import GoodsMovementReport
# from ..multiplicity_processor import miltiplicity_processing_excel
from ..data_cleaning import open_file
import io

class MyTestCase(unittest.TestCase):
    def test_something(self):
        CURRENT_DIR = Path(__file__).resolve().parent.parent / 'file_test'
        TEST_FILES = [file for file in CURRENT_DIR.glob('*.xlsx')]
        if not TEST_FILES:
            raise FileNotFoundError(f'No test files found in {CURRENT_DIR}')

        for file in TEST_FILES:
            print(file.name)
            # processor_type = get_processor('goods_movement')
            file_bytes = file.read_bytes()
            # processor = ProcessingPipeline(processor_type)
            # result = processor.run(file_bytes, file.name)
            # result = GoodsMovementReport(file_bytes, file.name).get_stream
            result = open_file(file_bytes, file.name)
            file_bytes_io = io.BytesIO(result)
            with open(CURRENT_DIR/f'{file.name}_результат.xlsx' , 'wb') as f:
                f.write(file_bytes_io.read())
            print('Анализ закончен. Результаты сохранены в файл')



if __name__ == '__main__':
    unittest.main()
