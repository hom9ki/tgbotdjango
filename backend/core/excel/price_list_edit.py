import io

from openpyxl import load_workbook, Workbook
import pandas
from pathlib import Path

from openpyxl.utils.dataframe import dataframe_to_rows

PRICE_SETTINGS = {
    'Спутник': ['Артикул', 'Бренд', 'Цена', 'Кол-во'],
    'МоскворечьеВИП': ['Производитель', 'Номер производителя', 'Наличие на складе', 'Цена, Рубль']

}


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


def read_excel(file_bytes, file_name):
    base_name = Path(file_name).stem
    if base_name not in PRICE_SETTINGS:
        print(f'Неизвестный файл {file_name}')
        return None
    columns = PRICE_SETTINGS[base_name]
    input_stream = io.BytesIO(file_bytes)
    workbook = load_workbook(input_stream, data_only=True)
    sheet = workbook.active

    data = list(sheet.values)

    header = data[0]
    rows = data[1:]

    df = pandas.DataFrame(rows, columns=header, index=None)
    print(df)

    existing_columns = [col for col in columns if col in df.columns]
    missing_columns = [col for col in columns if col not in df.columns]
    if len(missing_columns) > 0:
        print(f'Отсутствуют необходимые столбцы {missing_columns}')
        raise ValueError(f"Отсутствуют столбцы: {missing_columns}")

    print(existing_columns)

    df_new = df[existing_columns]

    output_wb = Workbook()
    output_sheet = output_wb.active

    output_sheet.append(columns)
    for row in dataframe_to_rows(df_new, index=False, header=False):
        output_sheet.append(row)

    output_stream = io.BytesIO()
    output_wb.save(output_stream)
    output_stream.seek(0)
    print('Обработка завершена')
    return output_stream.read()
