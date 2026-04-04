from django.shortcuts import render, reverse, get_object_or_404
from .models import UploadedFile
from .serializers import UploadedFileSerializer, FileUploadSerializer
from rest_framework.decorators import api_view, parser_classes, authentication_classes, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from users.models import CustomUser

from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_date
from .sevices import create_in_memory_uploaded_file

from .task import process_single_file_task
from celery.result import AsyncResult
from .utils.logging import logger

import base64


@login_required(login_url='/users/account/login/')
def index(request):
    """Главная страница"""
    user = request.user

    context = {
        'is_authenticated': user.is_authenticated,
        'username': user.username if user.is_authenticated else None,
    }
    return render(request, 'core/index.html', context)


@api_view(['POST'])
def api_file_save(request):
    """Сохранение файла"""
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
def api_upload_file(request, upload_type):
    """API для загрузки файла или списка файлов для обработки с помощью Celery"""
    logger.info(f'Запрос на обработку файлов: {request.data}')
    logger.info(f'Тип обработки: {upload_type}')
    files_list = request.FILES.getlist('files')
    if not files_list:
        return Response({
            'success': False,
            'error': {'files': 'Файлы не выбраны'},
        }, status=status.HTTP_400_BAD_REQUEST)
    task_result = []
    for file in files_list:
        _, file_bytes = create_in_memory_uploaded_file(file)
        file_bytes_b64 = base64.b64encode(file_bytes).decode('utf-8')
        task = process_single_file_task.delay(file_bytes_b64, file.name, upload_type)
        task_result.append({'filename': file.name, 'task_id': task.id})
    return Response({
        'success': True,
        'message': 'Обработка файлов начата',
        'tasks': task_result
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
def api_get_task_result(request, task_id):
    """Получение результата задачи"""
    task = AsyncResult(task_id, app=process_single_file_task.app)

    if task.status == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Ожидание обработки',
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
    else:
        response = {
            'state': task.state,
            'error': str(task.info)
        }
        return Response(response, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def api_get_form(request, form_type):
    """Получение формы для загрузки"""

    urls_types = {
        'multiplicity': 'Определение кратности',
        'price': 'Обработка прайс-листов',
        'goodsmove': 'Оптимизация ежедневных перемещений товаров'
    }

    upload_type = urls_types.get(form_type)
    logger.info(f'Тип формы обработки: {upload_type}')
    upload_url = None
    file_types = UploadedFile.types
    logger.info(f'Типы файлов: {file_types}')
    try:
        if upload_type:
            upload_url = reverse('api_upload', args=[form_type])
            logger.info(f'URL: {upload_url}')
            template = 'core/form_container.html'
        else:
            template = 'core/saved_form.html'

        context = {
            'csrf_token': request.META.get('CSRF_COOKIE'),
            'form_type': form_type,
            'file_types': file_types,
            'upload_url': upload_url
        }
        try:
            form_html = render_to_string(template, context, request=request)
            logger.info('Шаблон сформирован')
            return Response({
                'success': True,
                'form_html': form_html,
                'upload_url': upload_url,
                'title_form': upload_type

            }, status=status.HTTP_200_OK)
        except Exception as template_error:
            logger.error(f'Ошибка рендеринга шаблона: {template_error}', exc_info=True)
            raise
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['DELETE'])
def api_delete_file(request, file_id):
    """API для удаление файла по ID"""
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
    """Страница архива, доступная только авторизованным пользователям с переадресацией на страницу авторизации"""
    file_types = UploadedFile.types
    users = CustomUser.objects.all()
    return render(request, 'core/archive.html', {'file_types': file_types,
                                                 'users': users})


@api_view(['GET'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def api_search_files(request):
    """API для поиска файлов на странице архива"""
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
    """API для скачивания файла по ID"""
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
