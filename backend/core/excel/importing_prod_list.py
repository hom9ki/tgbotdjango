import pandas as pd
from django.db import transaction
from ..utils.logging import logger
from ..models import Nomenclature


def open_file(file):
    df = pd.read_excel(file)
    if df.empty:
        logger.warning('Дата фрейм пуст.')
        return None
    return clean_data(df)

def save_to_db(df:pd.DataFrame):
    manufactures = df['Производитель'].fillna('').astype(str).str.strip()
    catalogs = df['Номер по каталогу'].fillna('').astype(str).str.strip()
    names = df['Наименование'].fillna('').astype(str).str.strip()

    valid_mask = (manufactures != '') & (catalogs != '')
    manufactures = manufactures[valid_mask]
    catalogs = catalogs[valid_mask]
    names = names[valid_mask]

    if len(manufactures) == 0:
        logger.warning('Нет валидных строк (пустые ключи)')
        return {'created': 0, 'updated': 0}

    objects = [Nomenclature(manufacturer=m, catalog_number=c, name=n)
               for m, c, n in zip(manufactures, catalogs, names)]

    with transaction.atomic():
        Nomenclature.objects.bulk_create(
            objects,
            update_conflicts=True,
            unique_fields=['manufacturer', 'catalog_number'],
            update_fields=['name'],
            batch_size=500,

        )
    return {'toral', len(objects)}

def clean_data(df: pd.DataFrame):
    main_columns = ['Производитель', 'Номер по каталогу', 'Наименование']
    drop_col = [c for c in df.columns if c not in main_columns]
    try:
        df = df.drop(drop_col, axis=1)
        df = df.drop_duplicates(subset=['Производитель', 'Номер по каталогу'])
    except Exception as e:
        logger.error(f'Ошибка обработки: {e}')
    logger.info(df.columns)
    return df


def processing(file):
    df = open_file(file)
    result = save_to_db(df)
    return result
