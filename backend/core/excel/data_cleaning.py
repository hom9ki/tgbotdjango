import pandas as pd
import io
from .settings import UNNECESSARY_BRANDS

assort_path = 'D:/Работа/Тестовые данные'
assort_file_name = 'Ассортимент.xlsx'


def open_file(file_bytes: bytes, file_name: str) -> pd.DataFrame:
    df = pd.read_excel(io.BytesIO(file_bytes), header=None, skiprows=3, usecols=[1, 2, 3, 7])
    un_brands = UNNECESSARY_BRANDS
    assort_df = pd.read_excel(f'{assort_path}/{assort_file_name}', skiprows=1, usecols=[2, 3, 4])
    assort_df = assort_df[assort_df['Ассортимент'] == 'Г']
    brand_number_assort = assort_df.groupby('Производитель')['Номер по каталогу'].apply(list).to_dict()
    print(assort_df.head())
    numencl_data = df.to_dict('records')
    result_data = []
    for row in numencl_data:
        if pd.isna(row[7]):
            continue
        if brand_number_assort.get(row[1], None) and row[2] in brand_number_assort[row[1]]:
            continue
        if row[1].lower() not in un_brands:
            ordered_row = {
                'Бренд': row[1],
                'Номер по каталогу': row[2],
                'Наименование': row[3],
                'Склад': 1645,
                'Количество': row[7],
                'Комментарий': file_name.replace('.xlsx', '')

            }
            result_data.append(ordered_row)

    print(len(result_data))
    new_df = pd.DataFrame(result_data)
    output_stream = io.BytesIO()
    with pd.ExcelWriter(output_stream, engine='openpyxl') as writer:
        new_df.to_excel(writer, index=False, sheet_name='Лист1')
    output_stream.seek(0)
    return output_stream.read()
