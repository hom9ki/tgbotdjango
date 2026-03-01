from pathlib import Path

from django.shortcuts import render, redirect, get_object_or_404
from .models import UploadedFile
from .serializers import UploadedFileSerializer, FileUploadSerializer, MultiFileUploadSerializer
from rest_framework.decorators import api_view, parser_classes, authentication_classes, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from users.models import CustomUser
from .excel.price_list_edit import PriceListEdit
from django.core.files.uploadedfile import InMemoryUploadedFile
import io
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_date
from .sevices import get_file_information, create_in_memory_uploaded_file
from .excel.pipeline import ProcessingPipeline
from .excel.registry import get_processor, PROCESSORS
from .task import process_single_file_task
from celery.result import AsyncResult
from .utils.logging import logger

import base64

from .excel.multiplicity_report import miltiplicity_processing_excel


@login_required(login_url='/users/account/login/')
def index(request):
    user = request.user

    context = {
        'is_authenticated': user.is_authenticated,
        'username': user.username if user.is_authenticated else None,
    }
    return render(request, 'core/index.html', context)


@api_view(['POST'])
def api_file_save(request):
    saved_file = request.FILES.get('file')
    if not saved_file:
        return Response({
            'success': False,
            'error': {'file': 'Файл не выбран'}
        }, status=status.HTTP_400_BAD_REQUEST)

    serializer = FileUploadSerializer(
        data=request.data,
        context={'request': request}
    )

    if serializer.is_valid():
        uploaded_file = serializer.save()

        save_file = UploadedFileSerializer(uploaded_file, context={'request': request}).data
        return Response({
            'success': True,
            'message': 'Файл успешно обработан',
            'save_file': save_file
        })
    else:
        return Response({
            'success': False,
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def api_upload_file_return_original(request):
    upload_files = request.FILES.getlist('files')
    logger.info(f'Обработка файлов: {upload_files}')
    if not upload_files:
        return Response({
            'success': False,
            'error': {'files': 'Файл не выбран'},
        }, status=status.HTTP_400_BAD_REQUEST)

    processed_files = []
    uploaded_files_data = []
    user_processor_type = get_processor(request.data.get('processing_type'))

    print(f'Тип процессора: {user_processor_type}')
    for file in upload_files:
        try:
            uploaded_file, file_bytes = create_in_memory_uploaded_file(file)
            print(f'Файл: {uploaded_file}')
            pipeline = ProcessingPipeline(user_processor_type)
            print(f'Пайплайн: {pipeline}, {type(pipeline)}')
            processor_stream_bytes, metadata = pipeline.run(file_bytes, file.name)

            processor_filename = metadata.get('filename')
            processed_stream = io.BytesIO(processor_stream_bytes)
            file.seek(0)
            processed_uploaded_file = InMemoryUploadedFile(
                file=processed_stream,
                field_name='file',
                name=processor_filename,
                content_type=file.content_type,
                size=len(processor_stream_bytes),
                charset=None
            )
            data = get_file_information(processed_uploaded_file, request, 'other')

            if 'title' not in data:
                data['title'] = file.name.split('.')[0]
            serializer = FileUploadSerializer(data=data, context={'request': request})

            if serializer.is_valid():
                upload_file = serializer.save()
                uploaded_files_data.append(UploadedFileSerializer(upload_file, context={'request': request}).data)

                processed_files.append({
                    'filename': processor_filename,
                    'content': base64.b64encode(processor_stream_bytes).decode('utf-8'),
                    'content_type': file.content_type
                })
            else:
                return Response({
                    'success': False,
                    'error': serializer.errors,
                    'action': 'multiple',
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f'Ошибка обработки файла {file.name}: {str(e)}')
            return Response({
                'success': False,
                'error': {'file': f'Ошибка обработки: {str(e)}'}
            }, status=status.HTTP_400_BAD_REQUEST)
    return Response({
        'success': True,
        'message': 'Файлы успешно обработаны',
        'processed_files': processed_files,
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def api_upload_single_file(request):
    """Загрузка одного файла"""
    uploaded_file = request.FILES.get('file')
    print(f'Тип процессора: {request.FILES}')
    original_extension = Path(uploaded_file.name).suffix
    final_name = f'Кратность {original_extension}'
    if not uploaded_file:
        return Response({
            'success': False,
            'error': {'file': 'Файл не выбран'}
        }, status=status.HTTP_400_BAD_REQUEST)

    content_type = uploaded_file.content_type
    original_uploaded_file, file_bytes = create_in_memory_uploaded_file(uploaded_file)
    original_data = get_file_information(original_uploaded_file, request, 'nomenclature', 'оригинал')

    original_serializer = FileUploadSerializer(
        data=original_data, context={'request': request}
    )
    if original_serializer.is_valid():
        original_serializer.save()
    else:
        return Response({
            'success': False,
            'error': original_serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)
    user_type_processor = request.data.get('processing_type')
    processor_type = get_processor(user_type_processor)
    pipeline = ProcessingPipeline(processor_type)
    processed_file_bytes = miltiplicity_processing_excel(file_bytes)

    processed_stream = io.BytesIO(processed_file_bytes)
    uploaded_file.seek(0)
    processed_uploaded_file = InMemoryUploadedFile(
        file=processed_stream,
        field_name='file',
        name=final_name,
        content_type=uploaded_file.content_type,
        size=len(processed_file_bytes),
        charset=None
    )
    processed_file_base64 = base64.b64encode(processed_file_bytes).decode('utf-8')

    data = get_file_information(processed_uploaded_file, request, 'other')

    serializer = FileUploadSerializer(
        data=data,
        context={'request': request}
    )

    if serializer.is_valid():
        uploaded_file = serializer.save()
    else:
        print(serializer.errors)
        return Response({
            'success': False,
            'error': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)

    response_serializer = UploadedFileSerializer(uploaded_file, context={'request': request})

    return Response({
        'success': True,
        'message': 'Файл успешно обработан',
        'processed_file': {
            'filename': f"{final_name}",
            'content': processed_file_base64,
            'content_type': content_type,
        },
        'uploaded_file': response_serializer.data,
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def api_upload_multiple_files(request):
    """Загрузка нескольких файлов"""
    files_list = request.FILES.getlist('files')

    if not files_list:
        print('Файлы не выбраны')
        return Response({
            'success': False,
            'error': {'files': ['Файлы не выбраны']},
            'action': 'multiple',
        }, status=status.HTTP_400_BAD_REQUEST)

    processed_files = []
    uploaded_files_data = []
    # TODO: Добавить работу с файлами в которых есть ошибки
    error_files = []

    for up_file in files_list:
        print(f'Обработка файла: {up_file.name}')
        try:
            original_uploaded_file, original_bytes = create_in_memory_uploaded_file(up_file)

            original_data = get_file_information(original_uploaded_file, request, 'price', 'оригинал')

            original_serializer = FileUploadSerializer(data=original_data, context={'request': request})
            if original_serializer.is_valid():
                original_instance = original_serializer.save()
                uploaded_files_data.append(UploadedFileSerializer(original_instance, context={'request': request}).data)

            else:
                return Response({
                    'success': False,
                    'error': original_serializer.errors,
                    'action': 'multiple',
                }, status=status.HTTP_400_BAD_REQUEST)

            processor_type = get_processor('price_list')
            pipeline = ProcessingPipeline(processor_type)

            processor_stream_bytes, metadata = pipeline.run(original_bytes, up_file.name)
            processor_filename = metadata.get('filename')
            processed_stream = io.BytesIO(processor_stream_bytes)
            up_file.seek(0)

            processed_uploaded_file = InMemoryUploadedFile(
                file=processed_stream,
                field_name='file',
                name=processor_filename,
                content_type=up_file.content_type,
                size=len(processor_stream_bytes),
                charset=None
            )

            data = get_file_information(processed_uploaded_file, request, 'other')

            if 'title' not in data:
                data['title'] = up_file.name.split('.')[0]

            serializer = FileUploadSerializer(data=data, context={'request': request})

            if serializer.is_valid():
                uploaded_file = serializer.save()
                uploaded_files_data.append(UploadedFileSerializer(uploaded_file, context={'request': request}).data)

                processed_files.append({
                    'filename': f"{processor_filename}",
                    'content': base64.b64encode(processor_stream_bytes).decode('utf-8'),
                    'content_type': up_file.content_type,
                })
            else:
                return Response({
                    'success': False,
                    'error': serializer.errors,
                    'action': 'multiple',
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(f'Ошибка обработки файла {up_file.name}: {str(e)}')
            return Response({
                'success': False,
                'error': {'file': f'Ошибка обработки: {str(e)}'}
            }, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'success': True,
        'message': 'Файлы успешно обработаны',
        'processed_files': processed_files,
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def api_processing_files_using_celery(request):
    logger.info(f'Запрос на обработку файлов: {request.data}')
    files_list = request.FILES.getlist('files')
    if not files_list:
        return Response({
            'success': False,
            'error': {'files': 'Файлы не выбраны'},
        }, status=status.HTTP_400_BAD_REQUEST)
    processing_type = request.data.get('processing_type')
    task_result = []
    for file in files_list:
        _, file_bytes = create_in_memory_uploaded_file(file)
        file_bytes_b64 = base64.b64encode(file_bytes).decode('utf-8')
        task = process_single_file_task.delay(file_bytes_b64, file.name, processing_type)
        task_result.append({'filename': file.name, 'task_id': task.id})
    return Response({
        'success': True,
        'message': 'Файлы успешно обработаны',
        'tasks': task_result
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
def api_get_task_result(request, task_id):
    task = AsyncResult(task_id, app=process_single_file_task.app)

    if task.status == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Ожидание обработки'
        }
        return Response(response, status=status.HTTP_202_ACCEPTED)

    elif task.state == 'SUCCESS':
        result = task.result
        response = {
            'state': task.state,
            'success': result['success'],
            'meta': result['meta'],
            'file_content': result['file_content']
        }
        return Response(response, status=status.HTTP_200_OK)
    elif task.state == 'FAILURE':
        response = {
            'state': task.state,
            'error': str(task.info)
        }
        return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def api_get_form(request, form_type='single'):
    """Получение формы для загрузки"""
    logger.info(f'Тип формы: {form_type}')
    try:
        file_types = UploadedFile.types
        processing_types = PROCESSORS.keys()
        if form_type == 'multiple':
            template = 'core/price_form_container.html'
        elif form_type == 'single':
            template = 'core/multiplicity_form_container.html'
        elif form_type == 'goodsmove':
            template = 'core/goodsmove_form_container.html'
        else:
            template = 'core/saved_form.html'

        form_html = render_to_string(template, {
            'csrf_token': request.META.get('CSRF_COOKIE'),
            'form_type': form_type,
            'file_types': file_types,
            'processing_types': processing_types,
        }, request=request)

        return Response({
            'success': True,
            'form_html': form_html,
            'form_type': form_type,
            'file_types': file_types,
            'processing_types': processing_types

        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['DELETE'])
def api_delete_file(request, file_id):
    if request.method == 'DELETE':
        try:
            files = UploadedFile.objects.all()
            print([f'ID: {file.id}' for file in files])
            file_id = UploadedFile.objects.get(id=file_id)
            file_id.delete()
            return Response({
                'success': True,
                'message': 'Файл успешно удален'
            }, status=status.HTTP_204_NO_CONTENT)
        except UploadedFile.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Файл не найден'
            }, status=status.HTTP_404_NOT_FOUND)
    else:
        return Response({
            'success': False,
            'error': 'Метод не поддерживается'
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)


@login_required(login_url='/users/account/login/')
def archive(request):
    file_types = UploadedFile.types
    users = CustomUser.objects.all()
    return render(request, 'core/archive.html', {'file_types': file_types,
                                                 'users': users})


@api_view(['GET'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def api_search_files(request):
    user = request.user
    if not user.is_authenticated:
        return Response({
            'success': False,
            'error': 'Пользователь не авторизован'
        }, status=status.HTTP_403_FORBIDDEN)

    files = UploadedFile.objects.all()

    title = request.GET.get('title', '')
    doc_type = request.GET.get('doc_type', '')
    uploaded_by_id = request.GET.get('uploaded_by', '')
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')
    if title:
        files = files.filter(title__icontains=title)
    if doc_type:
        files = files.filter(doc_type=doc_type)
    if uploaded_by_id:
        files = files.filter(uploaded_by_id=uploaded_by_id)
    if from_date:
        parser = parse_date(from_date)
        files = files.filter(created_at__date__gte=parser)
    if to_date:
        parser = parse_date(to_date)
        files = files.filter(created_at__date__lte=parser)
    file_card_html = ""
    for file in files:
        card_html = render_to_string('core/file_card.html', {
            'file': file
        }, request=request)
        file_card_html += card_html
    return Response({
        'success': True,
        'html': file_card_html,
        'count': files.count()
    })


@api_view(['GET'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def api_download_file(request, file_id):
    uploaded_file = get_object_or_404(UploadedFile, id=file_id)
    if not request.user.is_authenticated:
        print('Пользователь не авторизован')
        return Response({
            'success': False,
            'error': 'Пользователь не авторизован'
        }, status=status.HTTP_403_FORBIDDEN)

    if not uploaded_file.file.storage.exists(uploaded_file.file.name):
        print('Файл не найден')
        return Response({'success': False, 'error': 'Файл не найден'},
                        status=status.HTTP_404_NOT_FOUND)

    download_url = request.build_absolute_uri(uploaded_file.file.url)

    return Response({
        'success': True,
        'file': {'name': uploaded_file.filename,
                 'download_url': download_url,
                 }
    }, status=status.HTTP_200_OK)
