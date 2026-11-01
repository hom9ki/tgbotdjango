import os
from os.path import exists
from pathlib import Path

import pandas as pd

MONTHS = {
    1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель', 5: 'Май', 6: 'Июнь', 7: 'Июль',
    8: 'Август', 9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'

}


def get_file_dir():
    SCRIPT_DIR = Path(__file__).parent
    dir_name = 'file_test'
    FILE_DIR = Path(SCRIPT_DIR) / dir_name
    print(SCRIPT_DIR, FILE_DIR)
    return FILE_DIR


def build_summary(df):
    print(df.head())
    lbl_base = 'ВРН продажи'
    lbl_reserve = 'Количество'
    lbl_base_sum = 'ВРН сумма'
    lbl_reserve_sum = 'Сумма ЦС'
    lbl_itog = 'Итог продажи'

    base_sku = df[lbl_base].sum()
    reserve_sku = df[lbl_reserve].sum()
    total_sku = base_sku + reserve_sku

    base_sum = df[lbl_base_sum].sum()
    reserve_sum = df[lbl_reserve_sum].sum()
    total_sum = base_sum + reserve_sum

    itog = df[lbl_itog].sum()
    sku_base_itog = base_sku / itog * 100
    sku_reserve_itog = reserve_sku / itog * 100
    sum_base_itog = base_sum / total_sum * 100
    sum_reserve_itog = reserve_sum / total_sum * 100

    # return pd.DataFrame({
    #     'Склады': ['Основной', 'Резервный', 'Итого'],
    #     'SKU': [base_sku, reserve_sku, total_sku],
    #     'SKU %': [base_sku / itog * 100, reserve_sku / itog * 100, 100],
    #     'Сумма': [base_sum, reserve_sum, total_sum],
    #     'Сумма %': [base_sum / total_sum * 100, reserve_sum / total_sum * 100, 100],
    # })
    return pd.DataFrame(
        {
            'Основной': [base_sku, sku_base_itog, base_sum, sum_base_itog],
            'ЦС': [reserve_sku, sku_reserve_itog, reserve_sum, sum_reserve_itog],
            'Итог': [total_sku, sku_base_itog + sku_reserve_itog, total_sum, sum_base_itog + sum_reserve_itog]
        }, index=['SKU', 'SKU%', 'Сумма', 'Сумма%']
    )


def get_month(dir, files):
    for file in files:
        if 'Продажи' in file:
            print(f'{dir}/{file}')
            df = pd.read_excel(f'{dir}/{file}', usecols=[6, 7], header=None, skiprows=1, nrows=1)
            value = int(df.iloc[0, 0].split('.')[1])
            month = MONTHS[value]

    return month


def save_to_excel(path, df, month):
    df.to_excel(f"{files_path}/Итог {month}.xlsx", index=False)


def update_base_sale(df):
    diff = df['Итог продажи']

    df = df[diff > 0].copy()

    return df


def create_sales(df):
    # result_df['ВРН продажи'] = result_df['Итог продажи'] - result_df['Количество'].fillna(0)
    diff = df['Итог продажи'] - df['Количество'].fillna(0)
    mask = diff < 0

    df['ВРН продажи'] = diff.clip(lower=0)

    df.loc[mask, 'Количество'] = df.loc[mask, 'Итог продажи'].astype(float)
    df['ВРН сумма'] = df['Стоймость'] * df['ВРН продажи']
    return None


def clean_to_num(series):
    """Безопасное преобразование в число"""
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

    return pd.to_numeric(s, errors='coerce')  # ← coerce, а не raise


def processing(dir, files):
    files, files_path = files, dir
    df_conf = {
        'Продажи': {'header': 3},
        'ЦС': {'usecols': range(5, 11)},
        'Матрица': {},
        'Ассортимент': {'header': 1}
    }

    df_masks = {}

    for file in files:
        f_name = Path(file).stem
        for name in df_conf:
            print(f_name, name)
            if name in f_name:
                df_masks[name] = pd.read_excel(f'{files_path}/{file}', **df_conf[name])
                print(df_masks[name])
            # print(f"✅ {name}: {df_masks[name].shape}")

    order = ['Продажи', 'ЦС', 'Матрица', 'Ассортимент']

    missing = [name for name in order if name not in df_masks]
    if missing:
        raise FileNotFoundError(f'Не загружены: {missing}')

    print(df_masks['Продажи'].columns.tolist())

    base_df, sec_df, three_df, four_df = [df_masks[name] for name in order]

    for col in [6, 7]:
        base_df.iloc[:, col] = clean_to_num(base_df.iloc[:, col])
    print(f'Было строк:{len(sec_df)}')
    print(f'Сумма Количество до: {sec_df['Количество'].sum()}')
    base_df = base_df.rename(columns={base_df.columns[1]: sec_df.columns[2],
                                      base_df.columns[2]: sec_df.columns[3],
                                      base_df.columns[3]: 'Номенклатура',
                                      base_df.columns[6]: 'Итог продажи',
                                      base_df.columns[7]: 'Итог сумма'})
    base_df = base_df.drop(columns=base_df.columns[[0, 4, 5, 8, 9]])
    print(base_df.columns.tolist())
    print(base_df.head())
    group_cols = [c for c in sec_df.columns if c not in ['№', 'Количество']]
    sec_df = sec_df.groupby(group_cols, as_index=False)['Количество'].sum()
    print(sec_df.groupby(['Производитель', 'Номер по каталогу']).size().value_counts())
    base_df = update_base_sale(base_df)
    base_df['Стоймость'] = base_df['Итог сумма'] / base_df['Итог продажи']
    print(f'Стало строк:{len(sec_df)}')
    print(f'Сумма Количество после: {sec_df['Количество'].sum()}')
    headers = [base_df.columns[0], base_df.columns[1]]
    cols_from_sec = ['Производитель', 'Номер по каталогу', 'Количество']
    cols_from_three = ['Производитель', 'Номер по каталогу', 'Склад']
    cols_from_four = ['Производитель', 'Номер по каталогу', 'Ассортимент']
    result_df = base_df.copy()
    for frame, cols in [
        (three_df, cols_from_three),
        (four_df, cols_from_four),
        (sec_df, cols_from_sec)]:
        result_df = result_df.merge(frame[cols], on=headers, how='left')
    create_sales(result_df)
    result_df['Сумма ЦС'] = result_df['Количество'] * result_df['Стоймость']
    result_df = result_df.iloc[:-1]
    with pd.option_context('display.float_format', '{:.2f}'.format):
        print(result_df)
    month = get_month(dir, files)
    save_to_excel(files_path, result_df, month)
    masks = [
        ('Общая:', pd.Series(True, index=result_df.index)),
        ('Матрица:', result_df['Склад'].notna()),
        ('Не матрица:', result_df['Склад'].isna()),
        ('Общая + ЛП:', result_df['Ассортимент'] == 'Л'),
        ('Общая + ГП:', result_df['Ассортимент'] == 'Г'),
        ('Матрица + ЛП:', (result_df['Склад'].notna()) & (result_df['Ассортимент'] == 'Л')),
        ('Матрица + ГП:', (result_df['Склад'].notna()) & (result_df['Ассортимент'] == 'Г')),
        ('Не матрица + ЛП:', (result_df['Склад'].isna()) & (result_df['Ассортимент'] == 'Л')),
        ('Не матрица + ГП:', (result_df['Склад'].isna()) & (result_df['Ассортимент'] == 'Г'))
    ]
    with pd.ExcelWriter(f"{files_path}/Итог {month}.xlsx", engine='openpyxl', mode='a',
                        if_sheet_exists='overlay') as writer:
        cur_row = 1
        for name, mask in masks:
            df_summ = build_summary(result_df[mask])
            df_summ.to_excel(writer, sheet_name='Итоги', index=True, startrow=cur_row)
            ws = writer.sheets['Итоги']
            cell = ws.cell(row=cur_row, column=1, value=name)
            cur_row += len(df_summ) + 3


if __name__ == '__main__':
    path_dir = get_file_dir()
    for subfolder in path_dir.iterdir():
        if not subfolder.is_dir():
            continue
        print('Обрабатываем папку', subfolder.name, '...')
        files_path = path_dir / subfolder
        excel_files = list(subfolder.glob('*.xlsx'))
        print('Найдены файлы:', excel_files)
        if not excel_files:
            print('В папке нет файлов Excel')
        names = [file.name for file in excel_files]
        processing(files_path, names)
