import pandas as pd
import numpy as np
import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum


class ColumnType(Enum):
    """Типы колонок, которые мы умеем определять"""
    BRAND = "brand"  # Бренд/производитель
    ARTICLE = "article"  # Артикул/код товара
    NAME = "name"  # Название товара
    PRICE = "price"  # Цена
    QUANTITY = "quantity"  # Количество/остаток
    CATEGORY = "category"  # Категория
    DESCRIPTION = "desc"  # Описание
    UNIT = "unit"  # Единица измерения
    CURRENCY = "currency"  # Валюта
    WEIGHT = "weight"  # Вес
    DIMENSIONS = "dimensions"  # Габариты
    UNKNOWN = "unknown"  # Неизвестно


@dataclass
class ColumnInfo:
    """Информация о колонке"""
    index: int  # Индекс колонки (0-based)
    name: Optional[str]  # Имя колонки (если есть заголовки)
    data_type: ColumnType  # Определенный тип данных
    confidence: float  # Уверенность (0-1)
    sample_values: List[Any]  # Примеры значений
    characteristics: Dict[str, Any]  # Характеристики колонки


class SmartColumnDetector:
    """Умный детектор колонок в прайс-листах"""

    # Регулярные выражения для определения типов
    PATTERNS = {
        ColumnType.ARTICLE: [
            r'^[A-Z0-9\-_\/\.]{3,20}$',  # ABC-123, 123/456
            r'^[A-Z]{2,4}\d{4,8}$',  # AB12345, XYZ789012
            r'^\d{6,12}$',  # 12345678
            r'^[A-Za-z]+\d+[A-Za-z]*$',  # ABC123DEF
        ],
        ColumnType.PRICE: [
            r'^\d+[\.,]?\d*$',  # 123, 123.45, 123,45
            r'^\d{1,3}(?:[ \.]?\d{3})*[\.,]?\d*$',  # 1 000, 1.000,50
            r'^[$\€\₽\£]?\s*\d+[\.,]?\d*$',  # $123.45, €1000
        ],
        ColumnType.BRAND: [
            r'^(SAMSUNG|LG|APPLE|XIAOMI|BOSCH|PHILIPS|SONY|LENOVO|ASUS|HP|'
            r'ACER|DELL|CANON|EPSON|NOKIA|HUAWEI|OPPO|VIVO|REALME|ONE PLUS|'
            r'ZTE|MICROSOFT|GOOGLE|AMAZON|TOSHIBA|SHARP|PANASONIC|'
            r'HITACHI|SIEMENS|ELECTROLUX|INDESIT|ARISTON|BEKO|'
            r'WHIRLPOOL|GORENJE|ZANUSSI|CANDY|HOTPOINT|ARISTON)$',
        ]
    }

    # Ключевые слова для определения по содержимому
    KEYWORDS = {
        ColumnType.BRAND: [
            # Международные бренды
            'samsung', 'lg', 'apple', 'xiaomi', 'huawei', 'oppo', 'vivo',
            'sony', 'panasonic', 'philips', 'bosch', 'siemens', 'whirlpool',
            'electrolux', 'indesit', 'ariston', 'beko', 'gorenje', 'zanussi',
            'candy', 'hotpoint', 'lenovo', 'asus', 'acer', 'dell', 'hp',
            'canon', 'epson', 'brother', 'dlink', 'tp-link', 'cisco',

            # Русские бренды
            'белоруссия', 'беларусь', 'россия', 'казахстан',
            'мвидео', 'ситилинк', 'юлмарт', 'озон', 'wildberries',
        ],
        ColumnType.NAME: [
            'см', 'дюйм', '"', 'мм', 'кг', 'гр', 'л', 'мл',  # Единицы измерения
            'черный', 'белый', 'синий', 'красный', 'зеленый', 'серый',  # Цвета
            'большой', 'маленький', 'средний', 'xl', 'l', 'm', 's',  # Размеры
            'пластик', 'металл', 'дерево', 'стекло', 'керамика',  # Материалы
            'смартфон', 'телевизор', 'холодильник', 'стиральная',  # Типы товаров
            'ноутбук', 'компьютер', 'монитор', 'клавиатура', 'мышь',
            'диван', 'кресло', 'стол', 'стул', 'кровать', 'шкаф',
        ],
        ColumnType.CATEGORY: [
            'электроника', 'бытовая', 'техника', 'компьютеры',
            'мебель', 'одежда', 'обувь', 'аксессуары',
            'инструменты', 'стройматериалы', 'автотовары',
            'детские', 'спорт', 'косметика', 'продукты',
        ],
        ColumnType.UNIT: [
            'шт', 'кг', 'г', 'л', 'мл', 'м', 'см', 'мм',
            'упак', 'компл', 'набор', 'пара', 'рулон',
        ],
    }

    def __init__(self):
        self.column_infos: List[ColumnInfo] = []

    def analyze_dataframe(self, df: pd.DataFrame) -> List[ColumnInfo]:
        """Анализирует DataFrame и определяет типы колонок"""
        self.column_infos = []

        for col_idx in range(len(df.columns)):
            col_name = df.columns[col_idx] if isinstance(df.columns, pd.Index) else f"col_{col_idx}"
            column_data = df.iloc[:, col_idx] # Получаем колонку как Series

            # Анализируем колонку
            col_info = self._analyze_column(col_idx, col_name, column_data)
            self.column_infos.append(col_info)

        # После анализа всех колонок делаем пост-обработку
        self._post_process_analysis()

        return self.column_infos

    def _analyze_column(self, col_idx: int, col_name: Any, column_data: pd.Series) -> ColumnInfo:
        """Анализирует одну колонку"""
        # Берем выборку данных (первые 100 непустых значений)
        sample = self._get_sample(column_data, 100)

        # Определяем базовые характеристики
        stats = self._calculate_statistics(column_data, sample)

        # Определяем тип колонки
        col_type, confidence = self._detect_column_type(col_name, sample, stats)

        return ColumnInfo(
            index=col_idx,
            name=str(col_name) if not pd.isna(col_name) else None,
            data_type=col_type,
            confidence=confidence,
            sample_values=sample[:5],  # Первые 5 значений для примера
            characteristics=stats
        )

    def _get_sample(self, column_data: pd.Series, n: int = 100) -> List[Any]:
        """Получает выборку непустых значений из колонки"""
        # Отбрасываем NaN и пустые строки
        non_null = column_data.dropna()
        if len(non_null) == 0:
            return []

        # Берем первые n значений, но также случайные из середины для репрезентативности
        sample_indices = list(range(min(50, len(non_null))))
        if len(non_null) > 100:
            # Добавляем случайные значения из середины
            mid_start = len(non_null) // 2 - 25
            sample_indices.extend(range(mid_start, mid_start + 50))

        sample = []
        for idx in sample_indices:
            if idx < len(non_null):
                val = non_null.iloc[idx]
                if isinstance(val, (int, float, str)):
                    sample.append(val)

        return sample[:n]

    def _calculate_statistics(self, column_data: pd.Series, sample: List[Any]) -> Dict[str, Any]:
        """Вычисляет статистические характеристики колонки"""
        if not sample:
            return {"empty": True}

        stats = {
            "total_count": len(column_data),
            "non_null_count": len(sample),
            "null_ratio": 1 - (len(sample) / len(column_data)) if len(column_data) > 0 else 1.0,
            "unique_count": len(set(sample)),
            "is_numeric": False,
            "is_integer": False,
            "is_string": False,
            "avg_length": 0,
            "contains_numbers": False,
            "contains_letters": False,
            "contains_special": False,
        }

        # Анализируем типы данных в выборке
        numeric_count = 0
        integer_count = 0
        string_count = 0
        total_length = 0
        has_numbers = False
        has_letters = False
        has_special = False

        for val in sample:
            if isinstance(val, (int, float, np.integer, np.floating)):
                numeric_count += 1
                if isinstance(val, (int, np.integer)):
                    integer_count += 1
                if isinstance(val, (float, np.floating)) and val.is_integer():
                    integer_count += 1
            elif isinstance(val, str):
                string_count += 1
                total_length += len(val)

                # Анализируем содержимое строки
                if any(c.isdigit() for c in val):
                    has_numbers = True
                if any(c.isalpha() for c in val):
                    has_letters = True
                if any(not c.isalnum() and not c.isspace() for c in val):
                    has_special = True

        stats["is_numeric"] = numeric_count / len(sample) > 0.8
        stats["is_integer"] = integer_count / len(sample) > 0.8
        stats["is_string"] = string_count / len(sample) > 0.8
        stats["avg_length"] = total_length / string_count if string_count > 0 else 0
        stats["contains_numbers"] = has_numbers
        stats["contains_letters"] = has_letters
        stats["contains_special"] = has_special
        stats["numeric_ratio"] = numeric_count / len(sample)
        stats["string_ratio"] = string_count / len(sample)

        # Дополнительно: медиана для чисел
        if stats["is_numeric"]:
            numeric_values = [v for v in sample if isinstance(v, (int, float))]
            if numeric_values:
                stats["median"] = np.median(numeric_values)
                stats["min"] = min(numeric_values)
                stats["max"] = max(numeric_values)

        return stats

    def _detect_column_type(self, col_name: Any, sample: List[Any], stats: Dict) -> Tuple[ColumnType, float]:
        """Определяет тип колонки с оценкой уверенности"""
        if not sample:
            return ColumnType.UNKNOWN, 0.0

        # Проверяем по названию колонки (если оно есть)
        col_name_str = str(col_name).lower() if not pd.isna(col_name) else ""
        name_based_type, name_confidence = self._detect_by_column_name(col_name_str)

        # Проверяем по содержимому
        content_based_type, content_confidence = self._detect_by_content(sample, stats)

        # Если оба метода согласны
        if name_based_type == content_based_type and name_based_type != ColumnType.UNKNOWN:
            confidence = (name_confidence + content_confidence) / 2
            return name_based_type, min(confidence, 1.0)

        # Если метод по названию уверен
        if name_confidence > 0.8:
            return name_based_type, name_confidence

        # Если метод по содержимому уверен
        if content_confidence > 0.7:
            return content_based_type, content_confidence

        # Если это числовая колонка
        if stats["is_numeric"]:
            # Определяем, что это за число: цена, количество, вес и т.д.
            return self._classify_numeric_column(sample, stats)

        # Если текстовая колонка
        if stats["is_string"]:
            # Определяем, что это за текст
            return self._classify_text_column(sample, stats)

        return ColumnType.UNKNOWN, 0.5

    def _detect_by_column_name(self, col_name: str) -> Tuple[ColumnType, float]:
        """Определяет тип колонки по её названию"""
        if not col_name:
            return ColumnType.UNKNOWN, 0.0

        col_name_lower = col_name.lower()

        # Словарь сопоставления названий колонок с типами
        name_mappings = {
            ColumnType.BRAND: ['бренд', 'brand', 'производитель', 'manufacturer', 'maker'],
            ColumnType.ARTICLE: ['артикул', 'article', 'код', 'code', 'sku', 'арт', 'art'],
            ColumnType.NAME: ['наименование', 'название', 'name', 'product', 'товар', 'item'],
            ColumnType.PRICE: ['цена', 'price', 'стоимость', 'cost', 'руб', 'usd', 'eur'],
            ColumnType.QUANTITY: ['количество', 'кол-во', 'quantity', 'qty', 'остаток', 'stock'],
            ColumnType.CATEGORY: ['категория', 'category', 'группа', 'group', 'тип', 'type'],
            ColumnType.DESCRIPTION: ['описание', 'description', 'характеристики', 'features'],
            ColumnType.UNIT: ['единица', 'unit', 'ед.изм', 'measure', 'размер'],
        }

        for col_type, keywords in name_mappings.items():
            for keyword in keywords:
                if keyword in col_name_lower:
                    confidence = 0.8 + (
                        0.2 if col_name_lower == keyword else 0)  # Выше уверенность при точном совпадении
                    return col_type, confidence

        return ColumnType.UNKNOWN, 0.0

    def _detect_by_content(self, sample: List[Any], stats: Dict) -> Tuple[ColumnType, float]:
        """Определяет тип колонки по содержимому"""
        # Проверка на АРТИКУЛЫ
        if self._is_likely_article(sample):
            return ColumnType.ARTICLE, 0.9

        # Проверка на ЦЕНЫ
        if self._is_likely_price(sample, stats):
            return ColumnType.PRICE, 0.85

        # Проверка на БРЕНДЫ
        if self._is_likely_brand(sample):
            return ColumnType.BRAND, 0.8

        # Проверка на НАЗВАНИЯ ТОВАРОВ
        if self._is_likely_product_name(sample, stats):
            return ColumnType.NAME, 0.75

        # Проверка на КАТЕГОРИИ
        if self._is_likely_category(sample):
            return ColumnType.CATEGORY, 0.7

        return ColumnType.UNKNOWN, 0.0

    def _is_likely_article(self, sample: List[Any]) -> bool:
        """Определяет, похожи ли данные на артикулы"""
        if len(sample) < 3:
            return False

        article_count = 0
        for val in sample:
            if pd.isna(val):
                continue

            val_str = str(val).strip()

            # Проверяем по регулярным выражениям
            for pattern in self.PATTERNS[ColumnType.ARTICLE]:
                if re.match(pattern, val_str, re.IGNORECASE):
                    article_count += 1
                    break

            # Дополнительные эвристики для артикулов
            # Артикулы обычно имеют длину 3-20 символов
            if 3 <= len(val_str) <= 20:
                # Содержат буквы и цифры
                has_letter = any(c.isalpha() for c in val_str)
                has_digit = any(c.isdigit() for c in val_str)
                if has_letter and has_digit:
                    article_count += 0.5

        return article_count / len(sample) > 0.6

    def _is_likely_price(self, sample: List[Any], stats: Dict) -> bool:
        """Определяет, похожи ли данные на цены"""
        if not stats.get("is_numeric", False):
            return False

        numeric_sample = [v for v in sample if isinstance(v, (int, float))]
        if len(numeric_sample) < 3:
            return False

        # Цены обычно в определенном диапазоне
        prices = np.array(numeric_sample)

        # Эвристики для цен:
        # 1. Часто имеют 2 знака после запятой
        decimal_parts = [abs(v - int(v)) for v in prices if isinstance(v, float)]
        if decimal_parts:
            two_decimal_count = sum(1 for d in decimal_parts if d > 0 and round(d, 2) == d)
            if two_decimal_count / len(decimal_parts) > 0.3:
                return True

        # 2. Часто округлены (оканчиваются на 00, 90, 99)
        rounded_endings = ['00', '90', '99', '50']
        rounded_count = 0
        for price in prices:
            price_str = f"{price:.2f}"
            if any(price_str.endswith(ending) for ending in rounded_endings):
                rounded_count += 1

        if rounded_count / len(prices) > 0.4:
            return True

        # 3. Типичные диапазоны цен
        median_price = np.median(prices)
        if 10 <= median_price <= 1000000:  # От 10 руб до 1 млн
            return True

        return False

    def _is_likely_brand(self, sample: List[Any]) -> bool:
        """Определяет, похожи ли данные на бренды"""
        brand_count = 0
        for val in sample:
            if pd.isna(val):
                continue

            val_str = str(val).strip().lower()

            # Проверяем по ключевым словам
            for brand_keyword in self.KEYWORDS[ColumnType.BRAND]:
                if brand_keyword in val_str:
                    brand_count += 1
                    break

            # Проверяем по регулярному выражению
            if re.match(self.PATTERNS[ColumnType.BRAND][0], val_str, re.IGNORECASE):
                brand_count += 1

        return brand_count / len(sample) > 0.3

    def _is_likely_product_name(self, sample: List[Any], stats: Dict) -> bool:
        """Определяет, похожи ли данные на названия товаров"""
        if not stats.get("is_string", False):
            return False

        # Названия товаров обычно длиннее 10 символов
        avg_len = stats.get("avg_length", 0)
        if avg_len < 10:
            return False

        # Проверяем по ключевым словам
        keyword_count = 0
        for val in sample:
            if not isinstance(val, str):
                continue

            val_lower = val.lower()
            for keyword in self.KEYWORDS[ColumnType.NAME]:
                if keyword in val_lower:
                    keyword_count += 1
                    break

        return keyword_count / len(sample) > 0.4

    def _is_likely_category(self, sample: List[Any]) -> bool:
        """Определяет, похожи ли данные на категории"""
        # Категории обычно имеют мало уникальных значений
        unique_values = len(set(str(v).lower() for v in sample if not pd.isna(v)))
        if unique_values / len(sample) > 0.5:  # Слишком много уникальных значений для категории
            return False

        # Проверяем по ключевым словам
        keyword_count = 0
        for val in sample:
            if pd.isna(val):
                continue

            val_lower = str(val).lower()
            for keyword in self.KEYWORDS[ColumnType.CATEGORY]:
                if keyword in val_lower:
                    keyword_count += 1
                    break

        return keyword_count / len(sample) > 0.3

    def _classify_numeric_column(self, sample: List[Any], stats: Dict) -> Tuple[ColumnType, float]:
        """Классифицирует числовую колонку"""
        numeric_values = [v for v in sample if isinstance(v, (int, float))]
        if not numeric_values:
            return ColumnType.UNKNOWN, 0.5

        values = np.array(numeric_values)
        median_val = np.median(values)

        # ЦЕНА: обычно в диапазоне 10-1,000,000, часто с копейками
        if 10 <= median_val <= 1000000:
            # Проверяем, есть ли копейки
            has_cents = any(isinstance(v, float) and not v.is_integer() for v in numeric_values)
            if has_cents:
                return ColumnType.PRICE, 0.85
            else:
                return ColumnType.PRICE, 0.7

        # КОЛИЧЕСТВО: обычно целые числа, не очень большие
        if stats.get("is_integer", False) and median_val <= 1000:
            return ColumnType.QUANTITY, 0.75

        # ВЕС: обычно небольшие числа с десятичными
        if median_val <= 100 and any(isinstance(v, float) for v in numeric_values):
            return ColumnType.WEIGHT, 0.6

        return ColumnType.UNKNOWN, 0.5

    def _classify_text_column(self, sample: List[Any], stats: Dict) -> Tuple[ColumnType, float]:
        """Классифицирует текстовую колонку"""
        avg_len = stats.get("avg_length", 0)

        # ОПИСАНИЕ: обычно длинный текст
        if avg_len > 100:
            return ColumnType.DESCRIPTION, 0.8

        # НАЗВАНИЕ: средняя длина, содержит спецификации
        if 20 <= avg_len <= 100:
            return ColumnType.NAME, 0.7

        # БРЕНД/КАТЕГОРИЯ: короткий текст
        if avg_len < 20:
            # Проверяем, не бренд ли это
            if self._is_likely_brand(sample):
                return ColumnType.BRAND, 0.75

            # Проверяем, не категория ли это
            if self._is_likely_category(sample):
                return ColumnType.CATEGORY, 0.7

            # АРТИКУЛ: короткий, содержит буквы и цифры
            if self._is_likely_article(sample):
                return ColumnType.ARTICLE, 0.8

        return ColumnType.UNKNOWN, 0.5

    def _post_process_analysis(self):
        """Пост-обработка результатов анализа"""
        # Убеждаемся, что критически важные колонки определены правильно
        self._resolve_ambiguities()

        # Если есть несколько колонок одного типа, выбираем лучшую
        self._select_best_candidates()

    def _resolve_ambiguities(self):
        """Разрешает неоднозначности между колонками"""
        # Если есть несколько колонок, претендующих на один тип,
        # выбираем ту, у которой выше уверенность

        type_to_columns = {}
        for col_info in self.column_infos:
            if col_info.data_type not in type_to_columns:
                type_to_columns[col_info.data_type] = []
            type_to_columns[col_info.data_type].append(col_info)

        # Для критически важных типов (цена, артикул) убеждаемся, что они определены правильно
        for critical_type in [ColumnType.PRICE, ColumnType.ARTICLE, ColumnType.NAME]:
            if critical_type in type_to_columns and len(type_to_columns[critical_type]) > 1:
                # Выбираем колонку с максимальной уверенностью
                best_col = max(type_to_columns[critical_type], key=lambda x: x.confidence)
                for col in type_to_columns[critical_type]:
                    if col != best_col:
                        # Меняем тип менее уверенных колонок
                        col.data_type = ColumnType.UNKNOWN
                        col.confidence = 0.5

    def _select_best_candidates(self):
        """Выбирает лучшие кандидаты для каждого типа"""
        # Приоритет типов колонок
        priority_order = [
            ColumnType.ARTICLE,
            ColumnType.PRICE,
            ColumnType.NAME,
            ColumnType.BRAND,
            ColumnType.QUANTITY,
            ColumnType.CATEGORY,
            ColumnType.DESCRIPTION,
            ColumnType.UNIT,
            ColumnType.UNKNOWN,
        ]

        # Собираем все колонки, кроме UNKNOWN
        candidates = [c for c in self.column_infos if c.data_type != ColumnType.UNKNOWN]

        # Сортируем по приоритету типа и уверенности
        candidates.sort(key=lambda x: (priority_order.index(x.data_type), -x.confidence))

        # Оставляем только лучшую колонку каждого типа
        seen_types = set()
        for col in candidates[:]:
            if col.data_type in seen_types:
                col.data_type = ColumnType.UNKNOWN
            else:
                seen_types.add(col.data_type)


class AutoPriceProcessor:
    """Автоматический процессор прайс-листов с автодетектом колонок"""

    def __init__(self):
        self.detector = SmartColumnDetector()
        self.mapping: Dict[str, int] = {}  # target_col -> source_index

    def process_file(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Обрабатывает файл с полным автодетектом"""
        # 1. Читаем файл (с автоопределением заголовков)
        df = self._read_file_with_auto_detect(file_bytes, filename)

        # 2. Анализируем колонки
        print("\n" + "=" * 60)
        print("АНАЛИЗ КОЛОНОК ФАЙЛА")
        print("=" * 60)
        column_infos = self.detector.analyze_dataframe(df)

        # 3. Показываем результаты анализа
        self._display_analysis_results(column_infos)

        # 4. Создаем автоматическое сопоставление
        self._create_auto_mapping(column_infos)

        # 5. Предлагаем пользователю подтвердить/скорректировать
        self._interactive_confirmation(df, column_infos)

        # 6. Применяем сопоставление
        result_df = self._apply_mapping(df)

        # 7. Сохраняем результат
        output_bytes = self._save_to_excel(result_df)

        return {
            'dataframe': result_df,
            'bytes': output_bytes,
            'mapping': self.mapping,
            'column_analysis': column_infos,
        }

    def _read_file_with_auto_detect(self, file_bytes: bytes, filename: str) -> pd.DataFrame:
        """Читает файл с автоопределением наличия заголовков"""
        # Упрощенная версия - можно использовать ваш существующий код
        from io import BytesIO

        file_ext = Path(filename).suffix.lower()

        if file_ext in ['.xlsx', '.xls']:
            # Пробуем прочитать с заголовками
            try:
                engine = 'openpyxl' if file_ext == '.xlsx' else 'xlrd'
                df_with_headers = pd.read_excel(BytesIO(file_bytes), engine=engine)

                # Простая эвристика: если первая строка содержит строки, а вторая - числа
                first_row_str_ratio = sum(isinstance(x, str) for x in df_with_headers.iloc[0]) / len(
                    df_with_headers.columns)
                if len(df_with_headers) > 1:
                    second_row_num_ratio = sum(isinstance(x, (int, float)) for x in df_with_headers.iloc[1]) / len(
                        df_with_headers.columns)
                    if first_row_str_ratio > 0.7 and second_row_num_ratio > 0.5:
                        return df_with_headers

                # Если не похоже на заголовки, читаем без них
                return pd.read_excel(BytesIO(file_bytes), engine=engine, header=None)
            except:
                return pd.read_excel(BytesIO(file_bytes), engine=engine, header=None)

        elif file_ext == '.csv':
            # Для CSV пробуем разные кодировки
            encodings = ['utf-8', 'cp1251', 'windows-1251']
            for encoding in encodings:
                try:
                    df = pd.read_csv(BytesIO(file_bytes), encoding=encoding, delimiter=';')
                    if len(df.columns) > 1:
                        return df
                except:
                    continue
            # Если не получилось, читаем без заголовков
            for encoding in encodings:
                try:
                    return pd.read_csv(BytesIO(file_bytes), encoding=encoding, delimiter=';', header=None)
                except:
                    continue

        raise ValueError(f"Не удалось прочитать файл {filename}")

    def _display_analysis_results(self, column_infos: List[ColumnInfo]):
        """Выводит результаты анализа колонок"""
        print("\nРЕЗУЛЬТАТЫ АНАЛИЗА:")
        print("-" * 80)
        print(f"{'№':<3} {'Название':<20} {'Тип':<15} {'Уверенность':<12} {'Примеры'}")
        print("-" * 80)

        for info in column_infos:
            col_name = info.name or f"col_{info.index}"
            examples = ", ".join(str(v)[:20] + "..." if len(str(v)) > 20 else str(v)
                                 for v in info.sample_values[:2])
            print(f"{info.index + 1:<3} {col_name:<20} {info.data_type.value:<15} "
                  f"{info.confidence:.1%<12} {examples}")

    def _create_auto_mapping(self, column_infos: List[ColumnInfo]):
        """Создает автоматическое сопоставление колонок"""
        # Целевые колонки, которые нам нужны (в порядке приоритета)
        target_columns = [
            ('Артикул', ColumnType.ARTICLE),
            ('Цена', ColumnType.PRICE),
            ('Название', ColumnType.NAME),
            ('Бренд', ColumnType.BRAND),
            ('Количество', ColumnType.QUANTITY),
            ('Категория', ColumnType.CATEGORY),
        ]

        self.mapping = {}
        used_indices = set()

        for target_name, target_type in target_columns:
            # Ищем колонку подходящего типа с максимальной уверенностью
            candidates = [
                info for info in column_infos
                if info.data_type == target_type
                   and info.index not in used_indices
                   and info.confidence > 0.5
            ]

            if candidates:
                # Выбираем лучшую колонку
                best_candidate = max(candidates, key=lambda x: x.confidence)
                self.mapping[target_name] = best_candidate.index
                used_indices.add(best_candidate.index)
                print(f"✓ Автоматически сопоставлено: колонка {best_candidate.index + 1} → '{target_name}'")
            else:
                print(f"✗ Не найдена подходящая колонка для '{target_name}'")

    def _interactive_confirmation(self, df: pd.DataFrame, column_infos: List[ColumnInfo]):
        """Интерактивное подтверждение сопоставления"""
        print("\n" + "=" * 60)
        print("ПОДТВЕРЖДЕНИЕ СОПОСТАВЛЕНИЯ")
        print("=" * 60)

        # Показываем первые строки данных
        print("\nПервые 3 строки данных:")
        print(df.head(3).to_string())

        print("\nПредложенное сопоставление:")
        for target_col, source_idx in self.mapping.items():
            col_name = column_infos[source_idx].name or f"col_{source_idx}"
            print(f"  {target_col} ← колонка {source_idx + 1} ({col_name})")

        # Предлагаем изменить
        while True:
            change = input("\nИзменить сопоставление? (y/n): ").lower()
            if change == 'n':
                break
            elif change == 'y':
                self._interactive_remapping(df, column_infos)
                break

    def _interactive_remapping(self, df: pd.DataFrame, column_infos: List[ColumnInfo]):
        """Интерактивное изменение сопоставления"""
        print("\nДоступные колонки:")
        for i, info in enumerate(column_infos):
            col_name = info.name or f"col_{i}"
            sample = ", ".join(str(v)[:15] for v in info.sample_values[:2])
            print(f"  {i + 1}. {col_name} [{info.data_type.value}] - {sample}")

        target_columns = ['Артикул', 'Цена', 'Название', 'Бренд', 'Количество', 'Категория']

        new_mapping = {}
        for target_col in target_columns:
            while True:
                choice = input(f"\nВыберите колонку для '{target_col}' (1-{len(column_infos)}, 0 - пропустить): ")
                if choice == '0':
                    break
                elif choice.isdigit() and 1 <= int(choice) <= len(column_infos):
                    source_idx = int(choice) - 1
                    new_mapping[target_col] = source_idx

                    # Показываем пример данных из выбранной колонки
                    sample_vals = df.iloc[:3, source_idx].tolist()
                    print(f"  Пример: {sample_vals}")
                    break
                else:
                    print("Неверный выбор. Попробуйте снова.")

        self.mapping = new_mapping

    def _apply_mapping(self, df: pd.DataFrame) -> pd.DataFrame:
        """Применяет сопоставление к DataFrame"""
        result_data = {}

        for target_col, source_idx in self.mapping.items():
            if source_idx < len(df.columns):
                result_data[target_col] = df.iloc[:, source_idx]
            else:
                result_data[target_col] = pd.Series([None] * len(df))

        # Добавляем все неиспользованные колонки в конец
        used_indices = set(self.mapping.values())
        for i in range(len(df.columns)):
            if i not in used_indices:
                col_name = f"Дополнительно_{i + 1}"
                result_data[col_name] = df.iloc[:, i]

        return pd.DataFrame(result_data)

    def _save_to_excel(self, df: pd.DataFrame) -> bytes:
        """Сохраняет DataFrame в Excel в памяти"""
        from io import BytesIO

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Данные')

            # Добавляем лист с информацией о сопоставлении
            mapping_df = pd.DataFrame([
                {'Целевая колонка': k, 'Исходная колонка': v + 1}
                for k, v in self.mapping.items()
            ])
            mapping_df.to_excel(writer, index=False, sheet_name='Сопоставление')

        output.seek(0)
        return output.read()


