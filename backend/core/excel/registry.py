from typing import Dict, Union

from .multiplicity_processor import MultiplicityProcessor
from .price_list_processor import PriceListProcessor
from .goods_movement_processor import GoodsMovementProcessor
from .base_excel_processor_V2 import ExcelProcessor

from .multiplicity_report import MultiplicityReport
from .price_list_edit import PriceListEdit
from .goods_movement_report import GoodsMovementReport

PROCESSORS = {
    'price': PriceListProcessor(),
    'multiplicity': MultiplicityProcessor(),
    'goodsmove': GoodsMovementProcessor()
}

PROCESSORS_V2 = {
    'price': PriceListEdit,
    'multiplicity': MultiplicityReport,
    'goodsmove': GoodsMovementReport
}


def get_processor(processor_type: str) -> Dict[str, Union[ExcelProcessor, str]]:
    type_processor = PROCESSORS_V2.get(processor_type)
    if not type_processor:
        raise ValueError(f'Неизвестный тип процессора: {processor_type}')
    return {'processor': ExcelProcessor(), 'type_processor': type_processor}
