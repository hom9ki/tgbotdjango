import pandas as pd
from ..utils.logging import logger
from ..models import Nomenclature, Completeness
from django.db import transaction


def open_file(file):
    logger.info(f'Открытие файла {file}')
    df = pd.read_excel(file)
    if df.empty:
        logger.warning('Дата фрейм пуст.')
        return None
    logger.info(f'Дата фрейм получен. Размер: {df.shape}')
    return clean_data(df)


def _lookup_nomenclature(keys, batch_size=500):
    from functools import reduce
    from operator import or_
    from django.db.models import Q

    result = {}
    for i in range(0, len(keys), batch_size):
        chunc = keys[i:i + batch_size]
        query = reduce(or_, (Q(manufacturer=m, catalog_number=c) for m, c in chunc))
        for nom in Nomenclature.objects.filter(query).only('id', 'manufacturer', 'catalog_number'):
            result[(nom.manufacturer, nom.catalog_number)] = nom
    return result


def save_to_db(keys, nom_by_key):
    not_found = [key for key in keys if key not in nom_by_key]
    if not_found:
        logger.warning(f'Не найдены номенклатуры: {not_found}')

    to_update = [
        Completeness(nomenclature_id=nom_by_key[key].pk, quantity=qty, active=True)
        for key, qty in keys.items()
        if key in nom_by_key
    ]

    if to_update:
        with transaction.atomic():
            Completeness.objects.bulk_create(to_update,
                                             update_conflicts=True,
                                             unique_fields=['nomenclature'],
                                             update_fields=['quantity', 'active', 'last_updated'],
                                             batch_size=500)

    stats = {
        'total': len(to_update),
        'not_found': len(not_found)
    }
    logger.info(f'Обновлено: {stats}')
    return stats


def clean_data(df):
    logger.info(f'Столбцы: {df.columns.tolist()}')
    logger.info(f'Данные: {df}')
    main_columns = ['Производитель', 'Номер по каталогу', 'Кратность']
    existing_columns = [col for col in df.columns.tolist() if col in main_columns]
    if existing_columns != main_columns:
        logger.warning(f'Отсутствуют необходимые колонки: {main_columns}. ')
        return None
    manufactures = df['Производитель'].fillna('').astype(str).str.strip()
    catalogs = df['Номер по каталогу'].fillna('').astype(str).str.strip()
    quantities = pd.to_numeric(df['Кратность'], errors='coerce').fillna(1)
    by_key = {}

    for m, c, q in zip(manufactures, catalogs, quantities):
        key = (m, c)
        by_key[key] = q

    return by_key


def set_multiplicity(file):
    keys = open_file(file)
    nom_by_key = _lookup_nomenclature(list(keys.keys()), batch_size=500)
    result = save_to_db(keys, nom_by_key)
    return result
