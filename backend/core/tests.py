from django.test import TestCase
from .excel.ple_v2 import SmartColumnDetector
import pandas as pd
from pathlib import Path


class TestSmartColumnDetector(TestCase):

    def test_create_data(self):
        CURRENT_DIR = Path(__file__).resolve().parent.parent / 'test_data' / 'excel'
        TEST_FILES = [file for file in CURRENT_DIR.glob('*.xlsx')]

        for file in TEST_FILES:
            print(file)
            df = pd.read_excel(file)

            processor = SmartColumnDetector()
            df = processor.analyze_df(df)
            print(df.head())
