import io

import pandas as pd
from pathlib import Path
from .settings import PRICE_SETTINGS, PRICE_NAMES, QUANTITY_KEYS
from .ple_v2 import SmartColumnDetector


class PriceListEdit:
    __PRICE_SETTINGS = PRICE_SETTINGS
    __PRICE_NAMES = PRICE_NAMES
    __ENCODINGS = ['utf-8', 'cp1251', 'windows-1251', 'iso-8859-1', 'latin1']
    __QUANTITY_KEYS = QUANTITY_KEYS

    def __init__(self, file_bytes: bytes, file_name: str):
        self.__file_bytes = file_bytes
        self.__file_name = file_name
        self.__extension = Path(file_name).suffix
        self.__base_name = Path(file_name).stem
        self.__columns = self.__PRICE_SETTINGS.get(self.__edit_name(), [])
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
        file_name = self.__edit_name()
        return f'{file_name}{self.__extension}'

    def __edit_name(self):
        words_file_name = self.__base_name.split('_')
        for key, value in self.__PRICE_NAMES.items():
            print(f'key: {key}, value: {value}')
            print(all(word in words_file_name for word in value))
            if all(word in words_file_name for word in value):
                print(f'Имя файла {self.__file_name} изменено на {key}')
                return key
        else:
            return self.__base_name

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
        columns = df.columns.tolist()

        new_columns = [''] * max(self.__max_count_col, len(columns))
        print(f'columns: {len(columns)}, new_columns: {len(new_columns)}, self.__columns: {self.__max_count_col}')
        rows = []

        first_column = set(df.iloc[:, 0].dropna().to_list())

        for i, col_name in enumerate(columns):
            print(new_columns)
            if col_name in self.__required_columns:
                print(f'col_name: {self.__columns[col_name]}, i: {i}')
                target_index = self.__columns[col_name] - 1
                new_columns[target_index] = col_name
                if i != target_index:
                    new_columns[i] = f'Column_{i}'
            else:
                if new_columns[i] in self.__required_columns:
                    continue
                else:
                    new_columns[i] = col_name

        match_columns = [col for col in new_columns if col in self.__required_columns]
        for i, col in enumerate(new_columns):
            if col in self.__required_columns and self.__columns[col] - 1 != i:
                new_columns[i] = f'Column_{i}'
        new_columns = [col for col in new_columns if pd.isna(col) != True]
        print(f'DF: {df.columns.tolist()}:\nnew_columns: {new_columns}\nmatch_columns: {match_columns}')

        for _, row in df.iterrows():
            if len([col for col in row.tolist() if pd.isna(col) != True]) < 2:
                continue
            rows.append({col: row.get(col) for col in new_columns})

        print(f'rows: {rows[:10]}')
        self.__data = rows

    def __read_file(self):
        new_df = None
        file_name = self.__edit_name()
        print(file_name)
        if file_name not in self.__PRICE_SETTINGS:
            print(f'Неизвестный файл {file_name}')
            self.__stream = None
        df = self.__read_file_data()
        headers = df.columns.tolist()
        print(f'Заголовки файла: {df.columns.tolist()}, {[str(col) for col in headers]}')
        if len([col for col in headers if 'Unnamed' not in str(col)]) < 3:
            for i, row in df[:10].iterrows():
                print(f'Значения в строке {i}:{row.tolist()}')
                row_values = row.tolist()
                print(type(row_values))
                if len([col for col in row_values if pd.isna(col) != True]) < 3:
                    print(f'Файл {self.__file_name} содержит не нужные столбцы {row}, в строке {i}, '
                          f'количество {len(['nan' == str(col).lower() for col in row_values])}')
                else:
                    df = df.iloc[i:]
                    df.columns = row_values
                    break

        missing_columns = [col for col in self.__required_columns if col not in df.columns]

        if len(missing_columns) == len(self.__required_columns):
            df = self.processor_header.analyze_df(df)
            new_df = self.__create_dataframe(df)
        elif len(missing_columns) == 1 and missing_columns[0] in self.__QUANTITY_KEYS:
            print(f'В прайсе {self.__file_name} не найден столбец с количество товара {missing_columns[0]}')
            df[missing_columns[0]] = 1
            print(df.head())
            new_df = self.__create_dataframe(df)
        elif missing_columns:
            raise ValueError(f'Отсутствуют необходимые столбцы: {missing_columns}')
        elif not missing_columns:
            columns = df.columns.tolist()

            col_position = {}
            for i, col in enumerate(columns):
                if col in self.__required_columns:
                    col_position[col] = i + 1

            if col_position == self.__columns:
                print(f'Столбцы в файле {self.__file_name} в правильном порядке')
                new_df = df
            else:
                new_df = self.__create_dataframe(df)

        output_stream = io.BytesIO()
        with pd.ExcelWriter(output_stream, engine='openpyxl') as writer:
            new_df.to_excel(writer, index=False, sheet_name='Лист1')
        output_stream.seek(0)
        self.__stream = output_stream.read()

    def __create_dataframe(self, df):
        self.__create_data(df)
        new_df = pd.DataFrame(self.__data)
        column_names = self.__get_header_names()

        new_df = new_df.rename(columns=column_names)

        return new_df

    def check_file_name(self):
        pass


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
