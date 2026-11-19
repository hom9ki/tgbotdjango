import pandas as pd
from django.db import transaction
from ..utils.logging import logger
from ..models import Nomenclature, Completeness
from .settings import key_words, anti_key_words, multiplicity
from tqdm import tqdm

tqdm.pandas()


def normalize_text(text):
    return str(text).lower().strip() if text else ''


def find_kit(product: str) -> bool:
    return any(kw in product for kw in ['комплект', 'набор', 'упаковка'])


def open_file(file):
    logger.info(f'Открытие файла {file}')
    df = pd.read_excel(file, header=1)
    if df.empty:
        logger.warning('Дата фрейм пуст.')
        return None
    logger.info(f'Дата фрейм получен. Размер: {df.shape}')
    return clean_data(df)


def multiplicity_process(nom):
    product = normalize_text(nom.name)
    number = normalize_text(nom.catalog_number)

    if find_kit(product):
        return 1
    if number.endswith(('l', 'r')) and not number.endswith('lr'):
        return 1
    if number.endswith('lr'):
        return 2

    result = 1

    for group, keywords in key_words.items():
        if any(word in product for word in keywords):
            anti_key = anti_key_words.get(group, [])
            normalized_product = product.replace('(', '').replace(')', '').split(' ')
            if anti_key and any(word in normalized_product for word in anti_key):
                return 1
            if anti_key:
                return multiplicity[group]
            result = multiplicity[group]

    return result


def save_to_db(df: pd.DataFrame) -> dict:
    logger.info('Сохранение в базу данных')
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
    logger.info(f'ID первой записи: {objects[0].pk}')
    logger.info(f'Номенклатура сохранена в базу данных. Количество: {len(objects)}')
    # df['Кратность'] = 1
    # df['Кратность'] = df.progress_apply(multiplicity_process, axis=1)
    # multi_df = df[df['Кратность'] != 1]
    # logger.info(f'Количество строк с не единичной кратностью: {len(multi_df)}')
    return {'total': len(objects), 'objects': objects}


def clean_data(df: pd.DataFrame):
    logger.info('Очистка данных')
    main_columns = ['Производитель', 'Номер по каталогу', 'Наименование']
    drop_col = [c for c in df.columns if c not in main_columns]
    try:
        df = df.drop(drop_col, axis=1)
        df = df.drop_duplicates(subset=['Производитель', 'Номер по каталогу'])
    except Exception as e:
        logger.error(f'Ошибка обработки: {e}')
    logger.info(f'Очистка данных завершена.\nОставшиеся столбцы: {df.columns}')
    return df


def save_multiplicity(objects: list):
    logger.info('Сохранение кратности')
    target = {}
    for nom in objects:
        try:
            qty = multiplicity_process(nom)
        except Exception as e:
            logger.error(f'Ошибка {e} при обработке {nom.name}')
            qty = 1
        target[nom.pk] = qty

    exists = {
        c.nomenclature_id: c for c in Completeness.objects.filter(nomenclature_id__in=target.keys())
    }

    to_update = []
    for nom_id, qty in target.items():
        c = exists.get(nom_id)
        if qty == 1:
            continue
        if not c.active_update:
            continue
        to_update.append(Completeness(nomenclature_id=nom_id, quantity=qty))

    if to_update:
        Completeness.objects.bulk_create(to_update,
                                         update_conflicts=True,
                                         unique_fields=['nomenclature'],
                                         update_fields=['quantity', 'last_updated'],
                                         batch_size=500)


def processing(file):
    df = open_file(file)
    result = save_to_db(df)
    save_multiplicity(result['objects'])
    return result
