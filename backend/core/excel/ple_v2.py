import pandas as pd
import numpy as np
import re
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Any, Dict


class ColumnType(Enum):
    BRAND = "brand"
    ARTICLE = 'article'
    NAME = 'name'
    PRICE = 'price'
    QUANTITY = 'quantity'
    UNDEFINED = 'undefined'


# @dataclass
# class ColumnInfo:
#     index: int
#     name: Optional[str]
#     data_type = ColumnType
#     confidence = float
#     sample_value: List[Any]
#     characteristics: Dict[str, Any]

@dataclass
class ColumnInfo:
    index: int
    data_type: ColumnType
    confidence: float
    data: List[Any] = None

    @classmethod
    def empty(cls):
        return cls(index=0, confidence=0.0, data_type=ColumnType.UNDEFINED)


class SmartColumnDetector:
    PATTERNS = {
        ColumnType.BRAND:
            [
                r'^[A-Z0-9\s&.-]+$'
            ],
        ColumnType.ARTICLE:
            [
                r'^[A-Z0-9\-_\/\.]{3,20}$',  # ABC-123, 123/456
                r'^[A-Z]{2,4}\d{4,8}$',  # AB12345, XYZ789012
                r'^\d{6,12}$',  # 12345678
                r'^[A-Za-z]+\d+[A-Za-z]*$',  # ABC123DEF
            ],
        ColumnType.PRICE:
            [
                r'^\d+[\.,]?\d*$',  # 123, 123.45, 123,45
                r'^\d{1,3}(?:[ \.]?\d{3})*[\.,]?\d*$',  # 1 000, 1.000,50
                r'^[$\€\₽\£]?\s*\d+[\.,]?\d*$',  # $123.45, €1000
            ],
        ColumnType.QUANTITY:
            [
                r'^\d+$',
                r'^[<>≥≤]\s*\d+$',
                r'^[<>≥≤]\d+$',
                r'^[<>≥≤]\s*\d+[\.,]\d+$'
            ],


    }

    def __init__(self):
        self.column_infos: List[ColumnInfo] = []
        self.column_types = {}

    def analyze_df(self, df: pd.DataFrame):

        if df.empty:
            print('df is empty')
            return None
        stat = {}
        print(df.head())
        for i, column in enumerate(df.columns):
            column_data = df.iloc[:, i]
            stat[i] = self.analyze_column(column_data, i, column, stat)

        columns_name = {col.index: col.data_type.value for col in self.detect_title(stat)}
        print(f'col_info: {columns_name}')

        return None

    def analyze_column(self, column_data: pd.Series, index: int, name: str, stat: dict):

        series = self.get_simple_series(column_data)
        type_res = self.simple_detect_column_type(series, index)
        if type_res['contain_str']:
            stat = self.detect_column_str_brand(series, index)
        elif type_res['contain_int']:
            stat = self.detect_column_int_brand(series, index)
        elif type_res['contain_float']:
            stat = self.detect_column_float_brand(series, index)
        else:
            print(type_res)
            raise ValueError('column type not found')
        data = self.select_title(stat)
        return data

    def get_simple_series(self, series: pd.Series) -> List[Any]:

        no_nan_series = series.dropna()
        if len(no_nan_series) == 0:
            return []
        simple_series = no_nan_series.sample(50, random_state=42).tolist()

        return simple_series

    def simple_detect_column_type(self, series: List[Any], index):
        stat_series = {
            'series_len': len(series),
            'contain_int': False,
            'contain_float': False,
            'contain_str': False,
            'percent_int': 0,
            'percent_float': 0,
            'percent_str': 0,
        }
        stat_values = {
            'int_count': 0,
            'float_count': 0,
            'str_count': 0,
        }

        for value in series:
            if isinstance(value, (int, np.integer)):
                stat_values['int_count'] += 1
            if isinstance(value, (float, np.floating)):
                stat_values['float_count'] += 1
            if isinstance(value, str):
                if value.isdigit():
                    stat_values['int_count'] += 1
                else:
                    try:
                        value = float(value.strip())
                        stat_values['float_count'] += 1
                    except ValueError:
                        stat_values['str_count'] += 1

        stat_series['contain_int'] = stat_values['int_count'] / stat_series['series_len'] > 0.5
        stat_series['contain_float'] = stat_values['float_count'] / stat_series['series_len'] > 0.5
        stat_series['contain_str'] = stat_values['str_count'] / stat_series['series_len'] > 0.7

        return stat_series

    def detect_column_str_brand(self, series: List[Any], index: int):
        result = []
        article_res = self.is_article(series, index)
        result.append(article_res)
        brand_res = self.is_brand(series, index)
        result.append(brand_res)
        return result

    def is_article(self, series: List[Any], index: int) -> ColumnInfo:
        confidence = 0
        for value in series:
            for pattern in self.PATTERNS[ColumnType.ARTICLE]:
                if re.match(pattern, str(value)):
                    confidence += 1
                    break
        return ColumnInfo(index=index, data_type=ColumnType.ARTICLE, confidence=confidence / len(series), data=series)

    def is_brand(self, series: List[Any], index: int) -> ColumnInfo:
        confidence = 0
        for value in series:
            for pattern in self.PATTERNS[ColumnType.BRAND]:
                if re.match(pattern, str(value)):
                    confidence += 1
                    break
        return ColumnInfo(index=index, data_type=ColumnType.BRAND, confidence=confidence / len(series), data=series)

    def detect_column_int_brand(self, series: List[Any], index: int) -> List[ColumnInfo]:
        result = []
        quantity_res = self.is_quantity(series, index)
        result.append(quantity_res)
        return result

    def is_quantity(self, series: List[Any], index: int) -> ColumnInfo:
        confidence = 0
        for value in series:
            for pattern in self.PATTERNS[ColumnType.QUANTITY]:
                if re.match(pattern, str(value)):
                    confidence += 1
                    break
        return ColumnInfo(index=index, data_type=ColumnType.QUANTITY, confidence=confidence / len(series),
                          data=series)

    def detect_column_float_brand(self, series: List[Any], index: int):
        result = []
        price_res = self.is_price(series, index)
        result.append(price_res)
        return result

    def is_price(self, series: List[Any], index: int) -> ColumnInfo:
        confidence = 0
        for value in series:
            for pattern in self.PATTERNS[ColumnType.PRICE]:
                if re.match(pattern, str(value)):
                    confidence += 1
                    break
        return ColumnInfo(index=index, data_type=ColumnType.PRICE, confidence=confidence / len(series), data=series)

    def select_title(self, stat: List[ColumnInfo]) -> ColumnInfo:
        if len(stat) <= 0:
            return ColumnInfo.empty()
        else:
            index = 0
            confidence = 0
            for i, item in enumerate(stat):
                if item.confidence > confidence:
                    confidence = item.confidence
                    index = i
            if confidence == 0:
                return ColumnInfo.empty()
            return stat[index]

    def detect_title(self, stat: dict):
        result = []

        if len(stat) <= 0:
            return None

        for key in self.PATTERNS.keys():
            lines = []
            for i in stat:
                if stat[i].data_type == key:
                    lines.append(stat[i])

            if len(lines) == 1:
                result.append(lines[0])
            if len(lines) > 1:
                if key == ColumnType.BRAND or key == ColumnType.ARTICLE:
                    result.extend(self.find_brand_and_article(lines))
                if key == ColumnType.PRICE:
                    result.extend(lines)
                    self.find_price(lines)
                if key == ColumnType.QUANTITY:
                    result.extend(self.find_quantity(lines))
                if key == ColumnType.UNDEFINED:
                    result.extend(lines)

        return result

    def find_brand_and_article(self, lines: List[ColumnInfo]):
        avg_len = {
            'line': None,
            'length': 0
        }
        for i, line in enumerate(lines):
            len_data = 0
            for value in line.data:
                len_data += len(str(value))
            if avg_len['line'] is None:
                avg_len['line'] = i
                avg_len['length'] = len_data / len(line.data)
            elif avg_len['length'] > len_data / len(line.data):
                avg_len['line'] = i
                avg_len['length'] = len_data / len(line.data)
            else:
                line.data_type = ColumnType.UNDEFINED

        for i, line in enumerate(lines):
            if i != avg_len['line']:
                line.data_type = ColumnType.UNDEFINED

        return lines

    def find_price(self, lines: List[ColumnInfo]):
        pass

    def find_quantity(self, lines: List[ColumnInfo]):
        avg_summ_data = {
            'line': None,
            'avg_summ': 0
        }

        for i, line in enumerate(lines):
            avg_data = sum([int(value.replace('>', '')) if type(value) == str else value for value in line.data]) / len(
                line.data)

            num_list = [int(value.replace('>', '')) if type(value) == str else value for value in line.data]

            if avg_summ_data['line'] is None and 1 in num_list:
                avg_summ_data['line'] = i
                avg_summ_data['avg_summ'] = avg_data
            elif avg_summ_data['avg_summ'] < avg_data and 1 in num_list:
                avg_summ_data['line'] = i
                avg_summ_data['avg_summ'] = avg_data
            else:
                line.data_type = ColumnType.UNDEFINED
        print(avg_summ_data)
        for i, line in enumerate(lines):
            if i != avg_summ_data['line']:
                line.data_type = ColumnType.UNDEFINED
        return lines
