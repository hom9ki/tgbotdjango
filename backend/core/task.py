import base64

from celery import shared_task
from .excel.pipeline import ProcessingPipeline
from .excel.registry import get_processor


@shared_task(max_retries=3)
def process_single_file_task(file_data_b64, file_name, processing_type):
    p_type = get_processor(processing_type)
    pipeline = ProcessingPipeline(p_type)
    file_bytes = base64.b64decode(file_data_b64)
    processing_result, meta = pipeline.run(file_bytes, file_name)
    if not isinstance(processing_result, (bytes, bytearray)):
        raise ValueError(f"processing_result должен быть bytes, получил: {type(processing_result)}")

    print(f'Processing result: {meta}')
    processing_result_base64 = base64.b64encode(processing_result).decode('utf-8')
    return {
        'success': True,
        'file_content': processing_result_base64,
        'meta': meta
    }
