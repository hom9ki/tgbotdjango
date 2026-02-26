import base64

from celery import shared_task
from .excel.pipeline import ProcessingPipeline

@shared_task(bind=True, max_retries=3)
def process_single_file_task(self,file_data_b64, file_name, processing_type):
    try:
        pipeline = ProcessingPipeline(processing_type)
        file_bytes = base64.b64encode(file_data_b64)
        processing_result, meta = pipeline.run(file_bytes, file_name)
        return {
            'success': True,
            'file_content': processing_result,
            'meta': meta
        }
    except Exception as e:
        raise self.retry(exc=e, countdown=5)