import unittest
from ..download_prices import get_basename, save_dir, control_duplicate_files
import os

class MyTest(unittest.TestCase):
    def test_split_filename(self):

        TEST_FILENAME = ['export_Ekaterinburg_Autofluids_RUB_RS47379',
        'export_Ekaterinburg_RUB_RS47379',
        'export_Minsk_RUB_RS47379',
        'export_Moskow_RUB_RS47379',
        'FORUM_AUTO_PRICE_KEM',
        'FORUM_AUTO_PRICE_KRSK',
        'FORUM_AUTO_PRICE',
        'FORUM_AUTO_PRICE_NSK',
        'FORUM_AUTO_PRICE_OMSK',
        'Price_0a8f-7f4e',
        'price_all_260803_1',
        'PriceTiss',
        'BERG_ar48_20260803_050005',
        'BERG_ar48_20260803_103006',
        'BERG_ar48_20260803_140005']

        for name in TEST_FILENAME:
            get_basename(name)

    def test_duplicate_name(self):
        files = os.listdir(save_dir)
        print(files)
        for file in files:
            result = control_duplicate_files(file, save_dir)
            print(result)