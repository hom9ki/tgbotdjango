import unittest
from pathlib import Path
from ..registry import get_processor
from ..pipeline import ProcessingPipeline
from ..goods_movement_report import GoodsMovementReport

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
            result = GoodsMovementReport(file_bytes, file.name).get_stream
            print(result)



if __name__ == '__main__':
    unittest.main()
