import io

import pandas as pd
from pathlib import Path
from .settings import PRICE_SETTINGS, PRICE_NAMES
from .ple_v2 import SmartColumnDetector


class PriceListEdit:
    __PRICE_SETTINGS = PRICE_SETTINGS
    __PRICE_NAMES = PRICE_NAMES
    __ENCODINGS = ['utf-8', 'cp1251', 'windows-1251', 'iso-8859-1', 'latin1']

    def __init__(self, file_bytes: bytes, file_name: str):
        self.__file_bytes = file_bytes
        self.__file_name = file_name
        self.__extension = Path(file_name).suffix
        self.__base_name = Path(file_name).stem
        self.__columns = self.__PRICE_SETTINGS.get(self.__base_name, [])
        self.__required_columns = [col for col in self.__columns.keys()]
        self.__max_count_col = max(self.__columns.values())
        self.__data = []
        self.__stream = None
        self.processor_header = SmartColumnDetector()

    @property
    def get_stream(self):
        if self.__stream is None:
            self.__read_file()
        return self.__stream

    @property
    def get_file_name(self):
        self.__edit_name()
        return self.__file_name

    def __edit_name(self):
        if self.__base_name in self.__PRICE_NAMES:
            self.__file_name = f'{self.__PRICE_NAMES[self.__base_name]}{self.__extension}'

    def __read_xlsx_xls(self):
        try:
            engine = 'openpyxl' if self.__extension == '.xlsx' else 'xlrd'
            df = pd.read_excel(io.BytesIO(self.__file_bytes), engine=engine)
            return df
        except Exception as e:
            print(f'Ошибка при чтении файла {self.__file_name}: {e}')
            raise

    def __read_csv(self):
        for encoding in self.__ENCODINGS:
            try:
                df = pd.read_csv(io.BytesIO(self.__file_bytes), encoding=encoding, delimiter=';', low_memory=False)
                return df
            except UnicodeDecodeError:
                continue
            except Exception as e:
                continue
        raise ValueError(f'Не удалось прочитать файл {self.__file_name}')

    def __read_file_data(self):
        if self.__extension in ['.xls', '.xlsx']:
            return self.__read_xlsx_xls()
        elif self.__extension == '.csv':
            return self.__read_csv()
        else:
            raise ValueError(f'Неизвестный формат файла {self.__file_name}')

    def __get_header_names(self):
        headrs_names = {}
        for col_name, col_index in self.__columns.items():
            headrs_names[f'Column_{col_index - 1}'] = col_name

        return headrs_names

    def __create_data(self, df):
        print(df.head())
        print(df.columns.tolist())
        columns = df.columns.tolist()
        new_columns = [''] * len(columns)
        rows = []
        # for index, col_name in enumerate(df.columns):
        #     if col_name in self.__required_columns:
        #         self.__data[f'Column_{self.__columns[col_name] - 1}'] = df.iloc[:, index]
        #     else:
        #         if index not in self.__columns.values():
        #             self.__data[f'Column_{index}'] = df.iloc[:, index]

        for i, col_name in enumerate(columns):
            if col_name in self.__required_columns:
                target_index = self.__columns[col_name] - 1
                new_columns[target_index] = col_name
                new_columns[i] = columns[target_index]
            else:
                if new_columns[i] == '':
                    new_columns[i] = col_name

        for _, row in df.iterrows():
            rows.append({col: row.get(col) for col in new_columns})

        print(f'DF: {df.columns.tolist()}:\nnew_columns: {new_columns}')
        self.__data = rows

    def __read_file(self):
        if self.__base_name not in self.__PRICE_SETTINGS:
            print(f'Неизвестный файл {self.__file_name}')
            self.__stream = None
        df = self.__read_file_data()
        missing_columns = [col for col in self.__required_columns if col not in df.columns]

        if len(missing_columns) == len(self.__required_columns):
            df = self.processor_header.analyze_df(df)
            self.__create_data(df)
        elif missing_columns:
            raise ValueError(f'Отсутствуют необходимые столбцы: {missing_columns}')
        elif not missing_columns:
            # for i in range(self.__max_count_col):
            #     self.__data[f'Column_{i}'] = [None] * len(df)
            self.__create_data(df)
        new_df = pd.DataFrame(self.__data)
        column_names = self.__get_header_names()
        # name_cols = [column_names.get(f'Column_{i}', f'Column_{i}') for i in range(len(df.columns))]

        new_df = new_df.rename(columns=column_names)
        # new_df.columns = name_cols
        output_stream = io.BytesIO()
        with pd.ExcelWriter(output_stream, engine='openpyxl') as writer:
            new_df.to_excel(writer, index=False, sheet_name='Лист1')
        output_stream.seek(0)
        self.__stream = output_stream.read()


def file_path():
    current_dir = Path(__file__).resolve().parent
    child_dir = ''.join(
        [child.name for child in current_dir.iterdir() if child.is_dir() and child.name != "__pycache__"])
    files = [files.name for files in current_dir.joinpath(child_dir).iterdir() if files.suffix == ".xlsx"]
    path = current_dir.joinpath(child_dir)
    print(path, files)
    data = {
        'files': files,
        'path': path
    }
    return data
