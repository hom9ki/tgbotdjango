import io

import pandas
from pathlib import Path
from .settings import PRICE_SETTINGS,PRICE_NAMES


def edit_file_name(file_name):
    if file_name in PRICE_NAMES.keys():
        file_name = PRICE_NAMES[file_name]
    return file_name



def read_xlsx(file_bytes, file_name, extension):
    try:
        engine = 'openpyxl' if extension == '.xlsx' else 'xlrd'
        df = pandas.read_excel(io.BytesIO(file_bytes), engine=engine)
        return df
    except Exception as e:
        print(f"Ошибка при чтении файла {file_name}: {e}")
        raise


def read_csv(file_bytes, file_name, encodings):
    for encoding in encodings:
        try:
            df = pandas.read_csv(io.BytesIO(file_bytes), encoding=encoding, delimiter=';', low_memory=False)
            return df
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"Ошибка при чтении файла {file_name} с кодировкой {encoding}: {e}")
            continue
    raise ValueError(f'Не удалось прочитать файл {file_name}')


def read_file_data(file_bytes, file_name):
    print(f'Чтение файла: {file_name}')
    extension = Path(file_name).suffix
    encodings = ['utf-8', 'cp1251', 'windows-1251', 'iso-8859-1', 'latin1']

    if extension in ['.xls', '.xlsx']:
        return read_xlsx(file_bytes, file_name, extension)

    elif extension == '.csv':
        return read_csv(file_bytes, file_name, encodings)

    else:
        raise ValueError(f'Неизвестный формат файла {file_name}')


def read_excel(file_bytes, file_name):
    print(f'Чтение файла: {file_name}')
    base_name = Path(file_name).stem
    if base_name not in PRICE_SETTINGS:
        print(f'Неизвестный файл {file_name}')
        return None

    columns = PRICE_SETTINGS[base_name]
    required_columns = list(columns.keys())
    print(f'Чтение файла {file_name} завершено')

    df = read_file_data(file_bytes, file_name)

    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Отсутствуют необходимые столбцы: {missing_columns}")

    max_col = max(columns.values())
    data = {}
    for i in range(max_col):
        data[f'Column_{i}'] = [None] * len(df)

    for col_name, col_index in columns.items():
        data[f'Column_{col_index - 1}'] = df[col_name].tolist()

    new_df = pandas.DataFrame(data)

    column_names = {}
    for col_name, col_index in columns.items():
        column_names[f'Column_{col_index - 1}'] = col_name

    new_df = new_df.rename(columns=column_names)

    output_stream = io.BytesIO()
    with pandas.ExcelWriter(output_stream, engine='openpyxl') as writer:
        new_df.to_excel(writer, index=False, sheet_name='Лист1')
    output_stream.seek(0)
    print(f'Обработка файла {file_name} завершена')
    return output_stream.read()


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
