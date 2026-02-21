from django.test import TestCase
from .excel.ple_v2 import SmartColumnDetector
from .excel.pipeline import ProcessingPipeline
from .excel.registry import get_processor
import pandas as pd
from pathlib import Path


class TestSmartColumnDetector(TestCase):

    # def test_create_data(self):
    #     CURRENT_DIR = Path(__file__).resolve().parent.parent / 'test_data' / 'excel'
    #     TEST_FILES = [file for file in CURRENT_DIR.glob('*.xlsx')]
    #
    #     for file in TEST_FILES:
    #         print(file)
    #         df = pd.read_excel(file)
    #
    #         processor = SmartColumnDetector()
    #         df = processor.analyze_df(df)
    #         print(df.head())

    def test_create_df_for_movement(self):
        CURRENT_DIR = Path(__file__).resolve().parent.parent / 'test_data' / 'excel'
        TEST_FILES = [file for file in CURRENT_DIR.glob('*.xlsx')]

        for file in TEST_FILES:
            print(file.name)
            processor_type = get_processor('goods_movement')
            file_bytes = file.read_bytes()
            processor = ProcessingPipeline(processor_type)
            result =processor.run(file_bytes, file.name)
