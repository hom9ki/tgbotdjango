from django.test import TestCase
from .excel.ple_v2 import SmartColumnDetector
import pandas as pd


class TestSmartColumnDetector(TestCase):

    def test_create_data(self):
        data = [
            ['f-a11103c3', 'a11103c3', 'FENOX', 'Амортизатор', 1276, 1],
            ['xair-afco197', 'afco197', 'AIRLINE', 'Ароматизатор Кофе в мешочке со спреем горячий шоколад (AFCO197)',
             204.36, 4],
            ['xfbs-fdsb-cb4r', 'fdsb-cb4r', 'FEBEST', 'ВТУЛКА ЗАДНЕГО СТАБИЛИЗАТОРА D18 FORD FOCUS II CB4 2008-2011',
             396, 1],
            ['xjik-cd22001', 'cd22001', 'JIKIU', 'Пыльник шруса Infiniti  Nissan', 1229, 1],
            ['xly-g32125r', 'g32125r', 'LYNXauto', 'Стойка амортизаторная передняя NISSAN Almera (N15) 1.4-2.0D 95-00',
             3113, 1],
            ['xm-h04-0958', 'h04-0958', 'METELLI', 'Цилиндр тормозной', 1323.61, 1],
            ['xma-17539a', '17539a', 'MALO', 'Патрубок масляного радиатора', 196.81, 2]
        ]

        files = [
            'D:/tests_data/МИКАДО.xlsx',
            'D:/tests_data/АрмтекВИП.xlsx',
        ]
        for file in files:
            df = pd.read_excel(file)

            processor = SmartColumnDetector()
            processor.analyze_df(df)
