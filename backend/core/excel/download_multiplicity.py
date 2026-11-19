import pandas as pd
import io

from ..models import Completeness
from ..utils.logging import logger

def get_data():
    noms = Completeness.objects.filter(quantity__gt=1).values(
        'nomenclature__manufacturer',
        'nomenclature__catalog_number',
        'quantity',
    )
    logger.info(f'Всего {len(noms)} номенклатур с кратностью больше 1')
    data = {'Бренд':[r['nomenclature__manufacturer'] for r in noms],
            'Номер по каталогу':[r['nomenclature__catalog_number'] for r in noms],
            'Кратность':[r['nomenclature__quantity'] for r in noms]}
    return data

def create_df(data: dict) -> pd.DataFrame:
    return pd.DataFrame.from_dict(data)


def build_file(df: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()

    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')

    buffer.seek(0)

    return buffer.getvalue()

def get_multiplicity():
    data = get_data()
    df = create_df(data)
    return build_file(df)