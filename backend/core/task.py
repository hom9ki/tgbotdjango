import base64

from celery import shared_task
from .excel.pipeline import ProcessingPipeline


@shared_task(bind=True, max_retries=3)
def process_single_file_task(file_data_b64, file_name, processing_type):
    pipeline = ProcessingPipeline(processing_type)
    file_bytes = base64.b64decode(file_data_b64)
    processing_result, meta = pipeline.run(file_bytes, file_name)
    processing_result_base64 = base64.b64encode(processing_result).decode('utf-8')
    return {
        'success': True,
        'file_content': processing_result_base64,
        'meta': meta
    }
