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


@dataclass
class ColumnInfo:
    index: int
    name: Optional[str]
    data_type = ColumnType
    confidence = float
    sample_value: List[Any]
    characteristics: Dict[str, Any]


class SmartColumnDetector:
    PATTERNS = {
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
            ]
    }

    KEYWORDS = {
        ColumnType.BRAND:
            [

            ],
        ColumnType.NAME:
            [

            ],
    }
    def __init__(self):
        self.column_infos: List[ColumnInfo] = []

        def analyze_df(df: pd.DataFrame):

            for i, column in enumerate(df.columns):
                column_data = df.iloc[:, i]
                col_info = analyze_column(column_data, i, column)

        def analyze_column(column_data: pd.Series, index: int, name: str) -> ColumnInfo:

            series = get_simple_series(column_data)


        def get_simple_series(series: pd.Series) -> List[Any]:

            no_nan_series = series.dropna()
            if len(no_nan_series) == 0:
                return []
            simple_series = no_nan_series.sample(50, random_state=42).tolist()

            return simple_series


