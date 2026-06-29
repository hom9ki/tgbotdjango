import math

import pandas as pd
import io

mounts_name = ['июнь 25', 'июль 25', 'авг. 25', 'сент. 25', 'окт. 25', 'нояб. 25', 'дек. 25', 'янв. 26', 'февр. 26',
               'март 26', 'апр. 26', 'май 26', 'июнь 26']

DEEP = {
    'A': 2,
    'B': 2,
    'C': 1,
    'D': 1,
}
ABC_RANK = {
    'A': 2,
    'B': 1.5,
    'C': 1,
    'D': 0.5,
}
LAST_MONTHS_RANK = {
    3: 1,
    2: 0.5,
    1: 0.3,
    0: 0.1,
}


def get_sales(row):
    return [row[mount] for mount in mounts_name if not pd.isna(row[mount])]


def goods_rank(row):
    sales = [row[mount] if not pd.isna(row[mount]) else 0 for mount in mounts_name]
    last_months = sales[-3:]
    last_months = [x for x in last_months if not pd.isna(x)]
    mounts = len(get_sales(row))
    mounts_rank = mounts / 13 if mounts else 0
    if not pd.isna(row['сумма + покуп.']) and row['сумма + покуп.'] in ABC_RANK.keys():
        abc_rank = ABC_RANK[row['сумма + покуп.']]
    else:
        abc_rank = 0
    avg_sales = calculate_sales(row, row['Кратн.'])
    avg_weigth = min(avg_sales / 1000, 2)

    rating = (abc_rank * 0.3 + mounts_rank * 0.4 + avg_weigth * 0.1 + LAST_MONTHS_RANK[len(last_months)] * 0.2) * 100
    return round(rating, 2)


def calculate_sales(row, multiplicity):
    sales = get_sales(row)
    if len(sales) == 0:
        return 0
    original_sales = [row[mount] if not pd.isna(row[mount]) else 0 for mount in mounts_name]
    last_months_sales = original_sales[-3:]
    if not last_months_sales:
        return 0

    max_sales = max(last_months_sales)
    round_sales = math.ceil(((sum(sales) / len(sales)) / multiplicity))
    avg_sales = max(max_sales, round_sales * multiplicity)
    return avg_sales


def calculate_sales_sender(row, deep=0):

    avg_sales = calculate_sales(row, row['Кратн.'])
    werehouse = row['Св. ост.']
    if werehouse == 0:
        print('Нет остатков')
        return 0
    if werehouse >= avg_sales * deep:
        excess = werehouse - avg_sales * deep
        print(f'Излишки: {excess}')
    else:
        excess = 0
    return excess


def calculate_sales_recipient(row):
    if pd.isna(row['Матрица']):
        return 0

    avg_sales = calculate_sales(row, row['Кратн.'])
    print(
        f'Cредняя продажа: {avg_sales}, Бренд: {row["Номенклатура Производитель"]}, Номенклатура: {row["№ по каталогу"]}, Склад: {row["Склад"]}')
    if not pd.isna(row['сумма + покуп.']) and row['сумма + покуп.'] in DEEP.keys():
        deep = DEEP[row['сумма + покуп.']]
    else:
        deep = 1
    if pd.isna(row['Св. ост.']) and pd.isna(row['В пути']):
        werehouse = 0
    elif pd.isna(row['Св. ост.']) and not pd.isna(row['В пути']):
        werehouse = row['В пути']
    elif not pd.isna(row['Св. ост.']) and pd.isna(row['В пути']):
        werehouse = row['Св. ост.']
    else:
        werehouse = row['Св. ост.'] + row['В пути']
    demand = ((avg_sales * deep - werehouse) // row['Кратн.']) * row['Кратн.']
    if demand < 0:
        return 0

    return demand


def distribute_goods(sender_df, recipient_df):
    total_surplus = sender_df['Излишки'].iloc[0]

    result_df = recipient_df.copy()
    result_df = result_df.sort_values('Ранг', ascending=False).reset_index(drop=True)

    result_df['Сред. продажа'] = result_df.apply(calculate_sales, axis=1, args=(result_df['Кратн.'].iloc[0],))
    result_df['Излишки'] = total_surplus
    result_df['покрыто'] = False
    result_df['остаток_потребности'] = result_df['Потребность'].copy()
    result_df['назначено'] = 0

    remaining_surplus = total_surplus

    for index, row in result_df.iterrows():
        if remaining_surplus <= 0:
            break

        need = row['остаток_потребности']
        if need > 0:
            allocation = min(need, remaining_surplus)
            result_df.at[index, 'назначено'] = allocation
            result_df.at[index, 'покрыто'] = allocation > 0
            result_df.at[index, 'остаток_потребности'] = need - allocation
            remaining_surplus -= allocation

    result_df['остаток_излишков'] = remaining_surplus

    return result_df, remaining_surplus


def read_file(file_bytes: bytes, file_name: str):
    df = pd.read_excel(io.BytesIO(file_bytes), header=1, usecols=range(35))  # usecol=range(10) ограничить колонки
    print(df.head())
    sender = input('Введите отправителя(пример: ДМД): ')
    werehouse_depth = int(input('Введите глубину склада в месяцах: '))
    unique_items = df.drop_duplicates(subset=['№ по каталогу'])[['Номенклатура Производитель', '№ по каталогу']]
    nomenclature_list = unique_items.rename(
        columns={'Номенклатура Производитель': 'brand', '№ по каталогу': 'nomenclature'}
    ).to_dict('records')
    nomenclature_list = [{**item, 'sender': sender} for item in nomenclature_list]

    all_distributed_dfa = []

    for item in nomenclature_list:
        sender_df = df[(df['Номенклатура Производитель'] == (item['brand'])) & (df['№ по каталогу'] == (item['nomenclature'])) &
                       (df['Склад'] == item['sender'])].copy()

        recipient_df = df[(df['Номенклатура Производитель'] == (item['brand'])) & (df['№ по каталогу'] == (item['nomenclature'])) &
                          (df['Склад'] != item['sender'])].copy()
        sender_df['Излишки'] = sender_df.apply(calculate_sales_sender, axis=1, args=(werehouse_depth,))
        recipient_df['Потребность'] = recipient_df.apply(calculate_sales_recipient, axis=1)
        recipient_df['Ранг'] = recipient_df.apply(goods_rank, axis=1)
        # print(sender_df.head())
        print(recipient_df)
        distributed_df, remaining_surplus = distribute_goods(sender_df, recipient_df)
        # print(distributed_df)
        all_distributed_dfa.append(distributed_df)

    fianl_df = pd.concat(all_distributed_dfa, ignore_index=True)

    output_stream = io.BytesIO()
    with pd.ExcelWriter(output_stream, engine='openpyxl') as writer:
        fianl_df.to_excel(writer, index=False, sheet_name='Лист1')
    output_stream.seek(0)
    return output_stream.read()
