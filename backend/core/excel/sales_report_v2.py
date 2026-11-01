import pathlib

import numpy as np
import pandas as pd
from pathlib import Path
import re

DATE_RE = re.compile(r'(\d{2}\.\d{2}\.\d{4})')

MONTHS = {
    1: 'January', 2: 'February', 3: 'March', 4: 'April',
    5: 'May', 6: 'June', 7: 'July', 8: 'August', 9: 'September',
    10: 'October', 11: 'November', 12: 'December'
}
MONTHS_RU = {
    'January': 'Январь', 'February': 'Февраль', 'March': 'Март', 'April': 'Апрель', 'May': 'Май', 'June': 'Июнь',
    'July': 'Июль', 'August': 'Август', 'September': 'Сентябрь', 'October': 'Октябрь', 'November': 'Ноябрь',
    'December': 'Декабрь'
}

ADD_DATA_PATH = Path('D:\Работа\Тестовые данные\Данные')

WAREHOUSES = {
    'ВРН': 'Воронеж Хранение',
    'КАЗ': 'Казань Хранение',
    'КРХ': 'КР Хранение',
    'КРС': 'Курск Хранение',
    'НН': 'Нижний Новгород Хранение',
    'НСК': 'Новосибирск Хранение',
    'РНД': 'Ростов-на-Дону Хранение',
    'СПБ': 'СПБ2 Хранение',
    'УФА': 'Уфа Хранение',
    'ЯРС': 'Ярославль Хранение'
}


def read_excel(path, mask) -> pd.DataFrame:
    path = Path(path)
    if not Path(path).exists():
        raise FileNotFoundError(f"Файл не найден: {path}")
    return pd.read_excel(path, **mask)


def ensure_not_empty(df: pd.DataFrame, message: str) -> pd.DataFrame or None:
    if df.empty:
        # raise ValueError(message)
        print(message)
        return None
    return df


def select_month_sheet(sheets, month):
    if month not in sheets:
        raise ValueError(f"В файле нет листа с месяцем: {month}")
    return ensure_not_empty(sheets[month], f"В файле нет данных по месяцу: {month}")


def filter_by_warehouse(df: pd.DataFrame, warehouse: str) -> pd.DataFrame:
    drop_columns = [col for col in df.columns.tolist() if
                    col in ['Номенклатура', 'Ассортимент', 'Вес нетто', 'Признак присвоения матрицы', 'Объем упаковки']]
    if 'Склад' not in df.columns:
        raise ValueError("В файле нет столбца 'Склад'")
    filtered_df = df[df['Склад'] == warehouse].drop(drop_columns, axis=1)

    return ensure_not_empty(filtered_df, f"В файле нет данных по складу: {warehouse}")


def open_file(path, mask, conf_matrix=None) -> pd.DataFrame:
    data = read_excel(path, mask)
    if conf_matrix is None:
        columns = data.columns.tolist()
        drop_columns = [col for col in columns if 'Unnamed' in col or col == 'Код']
        data = data.drop(drop_columns, axis=1)
        print(data.head(10))
        return ensure_not_empty(data, f"В файле нет данных: {path}")

    # add_data_df = select_month_sheet(data, conf_matrix['month'])
    return filter_by_warehouse(data, conf_matrix['warehouse'])


def get_add_data(wh_name, name):
    print(f'Загрузка дополнительных данных для {wh_name}: {name}')
    content_mask = {}
    if name in MONTHS_RU.keys():
        name = MONTHS_RU[name]
        content_mask = {
            'Матрица': {'warehouse': f'{WAREHOUSES[wh_name]}'}
        }
    elif name != 'Номенклатура':
        raise ValueError(f"Неверно указан месяц: {name}")
    conf_mask = {
        'Матрица': {},
        'Номенклатура': {'header': 1}
    }

    content = list(ADD_DATA_PATH.iterdir())
    add_data = {}
    df = pd.DataFrame()
    for f in content:
        if name in f.stem:
            df = open_file(f'{ADD_DATA_PATH}/{f.name}', conf_mask['Матрица'],
                           content_mask.get('Матрица', None))
            print(f'Файл {f.name} загружен')
        # if f.stem == 'Номенклатура':
        #     add_data[f.stem] = open_file(f'{ADD_DATA_PATH}/{f.name}', conf_mask[f.stem], content_mask.get(f.stem, None))

    # for f in content:
    #     if f.stem == 'Номенклатура':
    #         add_data[f.stem] = open_file(f'{ADD_DATA_PATH}/{f.name}', conf_mask[f.stem], content_mask.get(f.stem, None))
    #         print(f'Файл {f.name} загружен')
    #     elif 'матрица' in f.stem.lower():
    #         month = f.stem.split(' ')[1]
    #         add_data[month] = open_file(f'{ADD_DATA_PATH}/{f.name}', conf_mask['Матрица'],
    #                                     content_mask.get('Матрица', None))
    #         print(f'Файл {f.name} загружен')
    # add_data_keys = [k for k in add_data.keys()]
    # result = pd.merge(add_data[add_data_keys[1]], add_data[add_data_keys[0]], on=['Производитель', 'Номер по каталогу'],
    #                   how='left')
    return df


def clean_date(df):
    qty_col = [c for c in df.columns if c[1] == 'Кол-во']
    mask = (df[qty_col] > 0).any(axis=1)
    df_clean = df[mask].copy()
    return df_clean


def clean_to_num(series):
    """Безопасное преобразование в число"""
    print(f'Очищение столбцов {series.name} от лишних символов')
    s = (
        series.astype(str)
        .str.strip()
        .str.replace('\xa0', '', regex=False)
        .str.replace('\u2009', '', regex=False)
        .str.replace('\u202f', '', regex=False)
        .str.replace(' ', '', regex=False)
        .str.replace(',', '.', regex=False)
        .str.replace(r'[^\d.\-]', '', regex=True)  # оставляем цифры, точку, минус
    )

    s = s.where(~s.isin(['', '-', '.', '..', '--', '-.', '.-']), None)

    return pd.to_numeric(s, errors='coerce')


def get_months(df):
    top_level = df.columns.get_level_values(0).unique()
    return [m for m in top_level if DATE_RE.match(str(m))]


def add_price_col(df, month):
    qty_col = (month, 'Кол-во')
    sum_col = (month, 'Сумма')
    price_col = (month, 'Стоимость')

    if qty_col not in df.columns or sum_col not in df.columns:
        raise KeyError(f"Столбцы {qty_col} или {sum_col} не найдены в DataFrame")

    qty = df[qty_col]
    summ = df[sum_col]

    df[price_col] = np.where(qty > 0, (summ / qty), np.nan)

    return df


def add_central_sales(base_df, central_df, month, warehouse):
    group_cols = ['Производитель', 'Номер по каталогу']
    new_central_df = (central_df[central_df['Месяц'] == month].groupby(group_cols, as_index=False)['Количество'].sum()
                      .rename(columns={'Количество': 'ЦС_Кол-во'}))
    base_flat = base_df.copy()
    base_flat.columns = [f'{c[1]}' if isinstance(c, tuple) else c for c in base_flat.columns]

    merged_df = base_flat.merge(new_central_df, on=['Производитель', 'Номер по каталогу'],
                                how='left', validate='one_to_one')

    merged_df['ЦС_Кол-во'] = merged_df['ЦС_Кол-во'].fillna(0)
    merged_df['ЦС_Сумма'] = merged_df['ЦС_Кол-во'] * merged_df['Стоимость']

    # merged_df = merged_df.merge(get_add_data(warehouse, month), on=['Производитель', 'Номер по каталогу'])
    # merged_df = merged_df.drop(columns=['Номенклатура', 'Ассортимент'])

    return merged_df


def add_main_sales(df):
    diff = df['Кол-во'] - df['ЦС_Кол-во']
    mask = diff < 0

    df['Рег.склад_кол-во'] = diff.clip(lower=0)
    df.loc[mask, 'ЦС_Кол-во'] = df.loc[mask, 'Кол-во'].astype(int)
    df['ЦС_Сумма'] = df['ЦС_Кол-во'] * df['Стоимость']
    df['Рег.склад_сумма'] = df['Рег.склад_кол-во'] * df['Стоимость']

    # print(df.columns.tolist())
    # print(df.head(10))
    return df


def split_month(df, ):
    """Разбивает данные по месяцам"""
    months_conf = {
        1: 'January', 2: 'February', 3: 'March', 4: 'April',
        5: 'May', 6: 'June', 7: 'July', 8: 'August', 9: 'September',
        10: 'October', 11: 'November', 12: 'December'
    }

    result = {}
    months_cols = get_months(df)
    product_cols = [c for c in df.columns if str(c[0]) == 'Товар']

    for month in months_cols:
        columns_to_take = product_cols + [(month, m) for m in ('Кол-во', 'Сумма')]
        string_month = months_conf.get(int(month.split('.')[1]))
        # result[string_month] = df[columns_to_take]
        middle_res = df[columns_to_take].copy()
        middle_res = add_price_col(middle_res, month).iloc[:-1]

        result[string_month] = clean_date(middle_res)
    return result


def build_summary(df, name, group):
    print(f"📊 Сводка: {name} / {group}")
    lbl_base = 'Рег.склад_кол-во'
    lbl_reserve = 'ЦС_Кол-во'
    lbl_base_sum = 'Рег.склад_сумма'
    lbl_reserve_sum = 'ЦС_Сумма'

    required = [lbl_base, lbl_reserve, lbl_base_sum, lbl_reserve_sum]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"Нет колонок: {missing}. Есть: {df.columns.tolist()}")

    base_sku = df[lbl_base].sum()
    reserve_sku = df[lbl_reserve].sum()
    total_sku = base_sku + reserve_sku

    base_sum = df[lbl_base_sum].sum()
    reserve_sum = df[lbl_reserve_sum].sum()
    total_sum = base_sum + reserve_sum

    cs_percent = (df['ЦС_Сумма'].sum() / df['Сумма'].sum() * 100).round(2)
    base_percent = (df['Рег.склад_сумма'].sum() / df['Сумма'].sum() * 100).round(2)

    result = {
        'Месяц': name,
        'Группа': group,
        'Кол-во': total_sku,
        'Сумма': total_sum,
        'ЦС_Кол-во': reserve_sku,
        'ЦС_Сумма': reserve_sum,
        'Рег.склад_кол-во': base_sku,
        'Рег.склад_сумма': base_sum,
        'ЦС_%': f'{cs_percent}%',
        'Рег.склад_%': f'{base_percent}%'
    }
    return result


def get_file_dir():
    SCRIPT_DIR = Path(__file__).parent
    dir_name = 'file_test'
    FILE_DIR = Path(SCRIPT_DIR) / dir_name
    print(SCRIPT_DIR, FILE_DIR)
    return FILE_DIR


def add_add_data(df, add_data):
    merge_df = df.copy()
    merge_df = merge_df.merge(add_data, on=['Производитель', 'Номер по каталогу'], how='left')

    return merge_df


def build_res_mask(df, name):
    has_warehouse = 'Склад' in df.columns
    if has_warehouse:
        print('Полная')
        return [(df, name, 'Общая'),
                (df[df['Склад'].notna()], name, 'Матрица'),
                (df[df['Склад'].isna()], name, 'Не матрица'),
                (df[df['Ассортимент'] == 'Л'], name, 'Общая ЛП'),
                (df[(df['Склад'].notna()) & (df['Ассортимент'] == 'Л')], name, 'Матрица ЛП'),
                (df[(df['Склад'].isna()) & (df['Ассортимент'] == 'Л')], name, 'Не матрица ЛП'),
                (df[df['Ассортимент'] == 'Г'], name, 'Общая ГП'),
                (df[(df['Склад'].notna()) & (df['Ассортимент'] == 'Г')], name, 'Матрица ГП'),
                (df[(df['Склад'].isna()) & (df['Ассортимент'] == 'Г')], name, 'Не матрица ГП')]
    print('Не полная')
    return [
        (df, name, 'Общая'),
        (df[df['Ассортимент'] == 'Л'], name, 'Общая ЛП'),
        (df[df['Ассортимент'] == 'Г'], name, 'Общая ГП')
    ]


def processing(files_path, save_name, nomen_df):
    df_conf = {
        'Продажи': {'header': [1, 2]},
        'ЦС': {'usecols': lambda x: x != 'Проведен'},
        # 'Матрица': {},
        # 'Ассортимент': {'header': 1}
    }

    data = {}
    for file in files_path.iterdir():
        if file.is_file() and file.suffix == '.xlsx':
            for name in df_conf.keys():
                if name in file.name:
                    print(f'Открываем файл {file.name}')
                    df = open_file(f'{files_path}/{file.name}', df_conf[name])
                    # df = pd.read_excel(f'{files_path}/{file.name}', **df_conf[name])
                    data[name] = df
    # add_data = get_add_data(save_name)
    mount_sales = {}
    for name, df in data.items():
        if name == 'Продажи':
            empty_cols = df.columns[df.isna().all()].tolist()
            df = df.drop(columns=[c for c in df.columns if c in empty_cols])
            df.columns = pd.MultiIndex.from_tuples([
                ('Товар', 'Производитель'),
                ('Товар', 'Номер по каталогу'),
                ('Товар', 'Наименование'),
                *df.columns[3:]
            ])
            for col in df.columns:
                if col[0] != 'Товар' and col[0] != 'Итого':
                    df[col] = clean_to_num(df[col])
            mount_sales = split_month(df)
        elif name == 'ЦС':
            dates = df['Заявка'].str.extract(DATE_RE, expand=False)
            parse_dates = pd.to_datetime(dates, format='%d.%m.%Y', errors='coerce')
            df['Месяц'] = parse_dates.dt.month.map(MONTHS)
            start = df.columns.get_loc('Производитель')
            data[name] = df.iloc[:, start:]

    # for name, df in mount_sales.items():
    #     df = add_central_sales(df, data['ЦС'], name)
    #     mount_sales[name] = add_main_sales(df)

    output_file = Path(files_path) / f'Итог_{save_name}.xlsx'
    mode = 'w' if not output_file.exists() else 'a'

    monthly_total = []
    summary = []
    if Path(output_file).exists():
        Path(output_file).unlink()

    with pd.ExcelWriter(f'{files_path}/Итог_{save_name}.xlsx', engine='openpyxl', mode=mode,
                        if_sheet_exists='overlay' if mode == 'a' else None) as writer:

        for name, df in mount_sales.items():
            df = add_central_sales(df, data['ЦС'], name, save_name)
            df = add_main_sales(df)
            mont_df = get_add_data(save_name, name)
            if mont_df is not None:
                df = add_add_data(df, mont_df)
                res_mask = 'Полная'
            else:
                res_mask = 'Без матрицы'
            df = df.merge(nomen_df, on=['Производитель', 'Номер по каталогу'], how='left')
            # df = add_add_data(df, add_data['Номенклатура'])
            # df = add_add_data(df, add_data[MONTHS_RU[name]])

            print(f'Итоговые заголовки:{df.columns.tolist()}')
            df.to_excel(writer, sheet_name=name, index=False)

            # cs_percent = (df['ЦС_Сумма'].sum() / df['Сумма'].sum() * 100).round(2)
            # base_percent = (df['Рег.склад_сумма'].sum() / df['Сумма'].sum() * 100).round(2)

            # monthly_total.append({
            #     'Месяц': name,
            #     'Кол-во': df['Кол-во'].sum(),
            #     'Сумма': df['Сумма'].sum(),
            #     'ЦС_Кол-во': df['ЦС_Кол-во'].sum(),
            #     'ЦС_Сумма': df['ЦС_Сумма'].sum(),
            #     'Рег.склад_кол-во': df['Рег.склад_кол-во'].sum(),
            #     'Рег.склад_сумма': df['Рег.склад_сумма'].sum(),
            #     'ЦС_%': f'{cs_percent}%',
            #     'Рег.склад_%': f'{base_percent}%'
            # })
            masks = build_res_mask(df, name)
            for mask in masks:
                summary.append(build_summary(*mask))
            summary.append({'Месяц': '---', 'Группа': '---'})

        summary_df = pd.DataFrame(summary)
        summary_df.to_excel(writer, sheet_name='Итог', index=False, )


if __name__ == '__main__':
    path_dir = get_file_dir()
    for subfolder in path_dir.iterdir():
        if not subfolder.is_dir():
            continue
        print(f'Загрузка доп. номенклатуры из папки: {ADD_DATA_PATH}')
        nomenclature = open_file(ADD_DATA_PATH / 'Номенклатура.xlsx', {'header': 1})
        print(f'Обработка папки: {subfolder}')
        files_path = path_dir / subfolder
        excel_files = list(subfolder.glob('*.xlsx'))
        print(f'Найдены файлы: {excel_files}')
        processing(files_path, subfolder.name, nomenclature)
