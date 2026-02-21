import io
from io import BytesIO

import pandas as pd
from openpyxl import load_workbook, Workbook
from openpyxl.worksheet.worksheet import Worksheet

['Кратность', 'Кратность продажи', 'Остаток отпр', 'Дост Ост Отпр', 'Кол-во к перем.', 'К перемещению К']


class GoodsMovementReport:
    def __init__(self, file_bytes: bytes, file_name: str):
        self.file_name = file_name
        self.file_bytes = file_bytes

    @property
    def get_stream(self):
        """Получение потока"""""
        return self.read_file()

    @property
    def get_filename(self):
        """Получение имени файла"""
        return self.file_name

    def openpyxl_open_file(self, stream: io.BytesIO):
        """Открытие файла с помощью openpyxl для сохранения в тот же файл"""
        wb = load_workbook(stream)
        ws = wb.active
        return wb, ws

    def openpyxl_save_file(self, workbook: Workbook):
        output_stream = io.BytesIO()
        workbook.save(output_stream)
        output_stream.seek(0)
        return output_stream

    def openpyxl_update_file(self, data: dict, worksheet: Worksheet, df: pd.DataFrame):
        """Обновление файла"""
        headers_index = self.get_headers_index(df)
        for row_num, value_row in data.items():
            print(f'Строка {row_num}, значение {value_row}')
            cell = worksheet.cell(row=row_num, column=headers_index)
            cell.value = value_row

        return worksheet

    def pandas_open_file(self, stream: io.BytesIO):
        """Открытие файла с помощью pandas"""
        return pd.read_excel(stream)

    def adding_the_amount_of_movement(self, row: dict) -> None:
        """Добавление кол-ва перемещения в столбец К перемещению К"""
        if row['Кол-во к перем.'] != '':
            row['К перемещению К'] = row['Кол-во к перем.']

    def multiplicity_check(self, row: dict) -> None:
        """Проверка кратности"""
        amout = row.get('К перемещению К', 0)
        mult = row.get('Кратность продажи', 1)

        if mult != 1 and amout:
            remainder = amout % mult
            if remainder != 0:
                print(f'Остаток не кратен кратности, остаток {remainder}')
                row['К перемещению К'] = amout - remainder

    def stock_check(self, row: dict) -> None:
        """Проверка остатка"""
        stock = row.get('Остаток отпр', 0)
        mult = row.get('Кратность продажи', 1)
        available_balance = row.get('Дост Ост Отпр', 1)

        if stock < mult or available_balance < mult:
            print(f'Остаток меньше кратности')
            row['К перемещению К'] = ''

        elif stock < mult * 2:
            print(f'Остаток меньше кратности * 2')
            row['К перемещению К'] = ''

    def validate_inventory(self, rows: list) -> dict:
        """Проверка данных отчёта"""
        update_rows = {}
        for i, row in enumerate(rows, start=2):
            if row['Кол-во к перем.'] != '':
                self.adding_the_amount_of_movement(row)
                self.multiplicity_check(row)
                self.stock_check(row)
            update_rows[i] = row['К перемещению К']

        return update_rows

    def get_datafile(self, df: pd.DataFrame) -> dict:
        """Получение данных из файла"""
        rows = df.to_dict(orient='records')
        result = self.validate_inventory(rows)
        return result

    def del_nan(self, df: pd.DataFrame) -> pd.DataFrame:
        """Удаление NaN"""
        for col in df.columns:
            if col == 'Кратность продажи':
                df[col] = df[col].fillna(1)
            else:
                df[col] = df[col].fillna('')
        return df

    @staticmethod
    def get_headers_index(df: pd.DataFrame):
        return df.columns.tolist().index('К перемещению К') + 1

    def read_file(self) -> bytes:
        """Чтение файла"""
        input_stream = io.BytesIO(self.file_bytes)
        df = self.pandas_open_file(input_stream)
        input_stream.seek(0)
        workbook, worksheet = self.openpyxl_open_file(input_stream)
        input_stream.seek(0)
        df = self.del_nan(df)
        data = self.get_datafile(df)
        self.openpyxl_update_file(data, worksheet, df)
        output_stream = self.openpyxl_save_file(workbook)

        return output_stream.getvalue()
