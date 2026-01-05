import io

from openpyxl import load_workbook, Workbook
import pandas
from pathlib import Path

from openpyxl.utils.dataframe import dataframe_to_rows

PRICE_SETTINGS = {
    'Спутник': {'Артикул': 1, 'Бренд': 2, 'Цена': 4, 'Кол-во': 5},
    'МоскворечьеВИП': {'Производитель': 1, 'Номер производителя': 2,
                       'Наличие на складе': 6, 'Цена, Рубль': 5},
    'ТИСС МСК': {'Бренд': 1, 'Катал. номер': 3, 'ОПТ': 4, 'Кол-во всего': 5},
    'BERG НСК': {'Артикул': 1, 'Бренд': 3, 'Количество': 5, 'Цена руб': 6},
    'FORUM_AUTO_PRICE': {'ГРУППА': 1, '№ ПРОИЗВ.': 2, 'ЦЕНА, РУБ': 5, 'НАЛичие': 6},
    'PriceTiss': {'Бренд': 1, 'Катал. номер': 3, 'ОПТ': 8, 'Кол-во всего': 10},
    'Rossko': {'Бренд': 2, 'Артикул': 3, 'Цена, руб.': 7, 'Наличие': 9},
    'АвтоРусь': {'Артикул': 2, 'Изготовитель': 3, 'Наличие': 4, 'ЦенаКлиенту': 6},
    'БергВИП': {'Артикул': 1, 'Бренд': 3, 'Количество': 5, 'Цена руб': 6},
    'Иверс': {'Произв.': 1, 'Номер запчасти': 6, 'Ост.': 7, 'Цена': 8},
    'МХ групп': {'articul': 1, 'brand': 2, 'stock': 4, 'price': 5},
    'ПрофитЛига': {'Номенклатура.Производитель': 1, 'Артикул': 2, 'Цена': 6, 'ПредставлениеОстатка': 7},
    'РосскоВИП': {'Бренд': 2, 'Артикул': 3, 'Цена, руб.': 7},
    'Шате-М': {'Бренд': 1, 'Каталожный номер': 2, 'Остаток': 4, 'Цена': 7},
    'Шате-Подольск ВИП': {'Бренд': 1, 'Каталожный номер': 2, 'Остаток': 4, 'Цена': 7}

}


def read_excel(file_bytes, file_name):
    print('Чтение файла')
    base_name = Path(file_name).stem
    extension = Path(file_name).suffix
    if base_name not in PRICE_SETTINGS:
        print(f'Неизвестный файл {file_name}')
        return None

    columns = PRICE_SETTINGS[base_name]
    required_columns = list(columns.keys())
    print('Чтение файла завершено')
    print('Обработка файла')

    df = pandas.read_excel(io.BytesIO(file_bytes), engine='openpyxl')

    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Отсутствуют необходимые столбцы: {missing_columns}")
    print('Обработка файла')
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
    print('Обработка завершена')
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
