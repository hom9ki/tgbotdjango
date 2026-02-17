from .multiplicity_processor import MultiplicityProcessor
from .price_list_processor import PriceListProcessor

PROCESSORS = {
    'price_list': PriceListProcessor(),
    'multiplicity': MultiplicityProcessor(),
}


def get_processor(processor_type):
    processor = PROCESSORS.get(processor_type)
    if not processor:
        raise ValueError(f'Неизвестный тип процессора: {processor_type}')
    return processor
