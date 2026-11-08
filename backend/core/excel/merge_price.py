import pandas as pd
from pathlib import Path
import numpy as np

KEYS_COL = ['brand', 'catalog_number']

SCHEMA = {
    'brand': 'бренд',
    'catalog_number': 'каталожный номер',
    'name': 'наименование',
    'quantity': 'количество',

}

FILE_TYPES = [
    {
        'name': 'Rossko',
        'reader': pd.read_csv,
        'file_type': 'csv',
        'read_params': {
            'sep': ';',
            'encoding': 'cp1251',
            'decimal': '.',
        },
        'dtype': {
            'Бренд': str,
            'Артикул': str
        },
        'column_map': {
            'Бренд': 'brand',
            'Артикул': 'catalog_number',
            'Описание': 'name',
            'Наличие': 'quantity'
        },
        'required': ['Бренд', 'Артикул']
    },
    {
        'name': 'Автоконтракты',
        'reader': pd.read_csv,
        'file_type': 'csv',
        'read_params': {
            'sep': ';',
            'encoding': 'cp1251',
            'decimal': '.',
        },
        'dtype': {
            'Бренд': str,
            'Артикул': str
        },
        'column_map': {
            'Бренд': 'brand',
            'Артикул': 'catalog_number',
            'Описание': 'name',
            'Количество': 'quantity'
        },
        'required': ['Бренд', 'Артикул']
    },
    {
        'name': 'Автосоюз',
        'file_type': 'csv',
        'reader': pd.read_csv,
        'read_params': {
            'sep': ';',
            'encoding': 'utf-8',
            'decimal': '.',
            'header': 2,
        },
        'dtype': {
            'Производитель': str,
            'Артикул': str
        },
        'column_map': {
            'Производитель': 'brand',
            'Артикул': 'catalog_number',
            'Описание': 'name',
            'Остаток': 'quantity'
        },
        'required': ['Производитель', 'Артикул']
    },
    {
        'name': 'АПР',
        'file_type': 'csv',
        'reader': pd.read_csv,
        'read_params': {
            'sep': '\t',
            'encoding': 'cp1251',
            'decimal': '.',
        },
        'dtype': {
            'Бренд': str,
            'Нормированный код производителя': str,
        },
        'column_map': {
            'Бренд': 'brand',
            'Нормированный код производителя': 'catalog_number',
            'Наименование': 'name',
            'Количество': 'quantity',
        },
        'required': ['Бренд', 'Нормированный код производителя']
    },
    {
        'name': 'Иверс',
        'file_type': 'xlsx',
        'reader': pd.read_excel,
        'read_params': {
            'header': 0
        },
        'dtype': {
            'Произв.': str,
            'Код': str
        },
        'column_map': {
            'Произв.': 'brand',
            'Код': 'catalog_number',
            'Товар': 'name',
            'Ост.': 'quantity'
        },
        'required': ['Произв.', 'Код']
    },
    {
        'name': 'ФА',
        'file_type': 'csv',
        'reader': pd.read_csv,
        'read_params': {
            'sep': ';',
            'encoding': 'cp1251',
            'decimal': '.',
        },
        'dtype': {
            'марка': str,
            'каталожный номер': str
        },
        'column_map': {
            'марка': 'brand',
            'каталожный номер': 'catalog_number',
            'наименование детали': 'name',
            'количество на складе': 'quantity',
        },
        'required': ['марка', 'каталожный номер']
    }
]


def get_file_dir():
    SCRIPT_DIR = Path(__file__).parent
    dir_name = 'file_test'
    FILE_DIR = Path(SCRIPT_DIR) / dir_name
    print(SCRIPT_DIR, FILE_DIR)
    return FILE_DIR


def read_raw(file, folder):
    for ftype in FILE_TYPES:
        if ftype.get('name') == folder:
            try:
                df = ftype['reader'](file, **ftype['read_params'], dtype=ftype['dtype'])
                if all(c in df.columns for c in ftype['required']):
                    print(f'Файл {file} успешно прочитан')
                    print(f"Данные в файле: {df.head(10)}")

                    return df, ftype
            except Exception as e:
                print(f"Ошибка чтения {file}: {e}")
                continue
    raise ValueError(f"Не удалось прочитать файл: {file}")


def normalize_df(df, fty):
    new_df = df.copy()
    new_df.rename(columns=fty.get('column_map'), inplace=True)

    new_df['quantity'] = (
        pd.to_numeric(new_df['quantity'], errors='coerce')
        .fillna(0)
        .astype(int)
    )

    keep = [c for c in SCHEMA if c in new_df.columns]
    missing = [c for c in SCHEMA if c not in new_df.columns]
    print(f'{missing}: даные колонки отсутствуют')
    new_df = new_df[keep]
    print(f"   ✅ {len(new_df)} строк × {len(new_df.columns)} колонок")
    return new_df


def merge_stocks(files, folder):
    dfs = []

    for file in files:
        name = file.stem
        df, fty = read_raw(file, folder)
        print(df.head(5), fty)
        df = normalize_df(df, fty)
        df['_source'] = name
        dfs.append(df)
        print(f"📂 {file.name}: {len(df)} строк")

    combined = pd.concat(dfs, ignore_index=True)
    print(f"📊 Всего строк: {len(combined)}")

    pivot = combined.pivot_table(
        index=KEYS_COL,
        columns='_source',
        values='quantity',
        aggfunc='sum',
        fill_value=0
    ).add_prefix('количество_')
    other_col = [col for col in combined.columns
                 if col not in list(SCHEMA.keys()) + ['количество на складе', '_source']]

    base = combined.groupby(KEYS_COL, as_index=False)[other_col].first()
    drop_col = [col for col in base.columns if col not in SCHEMA.keys()]
    base = base.drop(drop_col, axis=1)

    result = count_changes(base.merge(pivot.reset_index(), on=KEYS_COL, how='left'))
    return result


def save_res(result, file_dir):
    save_name = file_dir / file_dir.name
    result.to_excel(f'{save_name}.xlsx', index=False)


def count_changes(df):
    qty_col = [col for col in df.columns if col.startswith('количество_')]

    if len(qty_col) < 2:
        df['снижение'] = 0
        df['повышение'] = 0

    qty = df[qty_col].fillna(0).values
    diff = np.diff(qty, axis=1)

    df['снижение'] = (diff < 0).sum(axis=1)
    df['повышение'] = (diff > 0).sum(axis=1)

    df = df[df['снижение'] > 0]

    return df


if __name__ == '__main__':
    file_dir = get_file_dir()
    if file_dir:
        print(f'Найден каталог: {file_dir}')
    else:
        print(f'Каталог не найден.')

    for subfolder in file_dir.iterdir():
        print(subfolder)
        # files = list(subfolder.glob('*.csv'))
        files = [f for f in subfolder.iterdir() if f.is_file()]
        print(files)
        res = merge_stocks(files, subfolder.name)
        save_res(res, subfolder)
