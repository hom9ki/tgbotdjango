from pathlib import Path

import openpyxl
from django.shortcuts import render
from .models import UploadedFile
from .serializers import UploadedFileSerializer, FileUploadSerializer, MultiFileUploadSerializer
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from .excel.price_list_edit import read_excel
from django.core.files.uploadedfile import InMemoryUploadedFile
import io

import base64

from .excel.multiplicity_report import miltiplicity_processing_excel


def index(request):
    user = request.user
    if user.is_authenticated:
        user_files = UploadedFile.objects.all()
        total_files = user_files.count()
    else:
        user_files = UploadedFile.objects.filter(uploaded_by__isnull=True)
        total_files = user_files.count()

    print(user_files)
    context = {
        'is_authenticated': user.is_authenticated,
        'username': user.username if user.is_authenticated else None,
    }
    return render(request, 'core/index.html', context)


@api_view(['GET'])
def api_get_files(request):
    """Список всех файлов"""
    user = request.user
    if user.is_authenticated:
        files = UploadedFile.objects.filter(uploaded_by=user).order_by('-created_at')
    else:
        files = UploadedFile.objects.filter(uploaded_by__isnull=True).order_by('-created_at')

    serializer = UploadedFileSerializer(
        files, many=True, context={'request': request}
    )
    return Response({
        'success': True,
        'files': serializer.data,
        'count': len(serializer.data)
    })


@api_view(['GET'])
def api_get_files_html(request):
    user = request.user
    if user.is_authenticated:
        files = UploadedFile.objects.filter(uploaded_by=user).order_by('-created_at')
    else:
        files = UploadedFile.objects.filter(uploaded_by__isnull=True).order_by('-created_at')

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
def api_upload_single_file(request):
    """Загрузка одного файла"""

    uploaded_file = request.FILES.get('file')
    print(uploaded_file)
    title = request.POST.get('title', '')
    original_date = title.split(' ')[2]
    original_extension = Path(uploaded_file.name).suffix
    final_name = f'Кратность {original_date}{original_extension}'
    print(f'{original_date}-{original_extension}: {final_name}')
    if not uploaded_file:
        return Response({
            'success': False,
            'error': {'file': 'Файл не выбран'}
        }, status=status.HTTP_400_BAD_REQUEST)

    content_type = uploaded_file.content_type

    file_bytes = uploaded_file.read()

    try:
        processed_file_bytes = miltiplicity_processing_excel(file_bytes)
        processed_stream = io.BytesIO(processed_file_bytes)
        uploaded_file.seek(0)
    except Exception as e:
        return Response({
            'success': False,
            'error': {'file': f'Ошибка обработки: {str(e)}'}
        }, status=status.HTTP_400_BAD_REQUEST)

    processed_uploaded_file = InMemoryUploadedFile(
        file=processed_stream,
        field_name='file',
        name=final_name,
        content_type=uploaded_file.content_type,
        size=len(processed_file_bytes),
        charset=None
    )
    processed_file_base64 = base64.b64encode(processed_file_bytes).decode('utf-8')

    print(request.data)

    data = {
        'file': processed_uploaded_file,
        'title': request.data.get('title', ''),
        'description': request.data.get('description', ''),
        'doc_type': request.data.get('doc_type', 'other'),
        'should_compress': request.data.get('should_compress', False)
    }

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

    for up_file in files_list:
        print(f'Обработка файла: {up_file.name}')
        try:
            up_file.seek(0)
            file_bytes = up_file.read()

            processed_file_bytes = read_excel(file_bytes, up_file.name)
            processed_stream = io.BytesIO(processed_file_bytes)
            up_file.seek(0)

            processed_uploaded_file = InMemoryUploadedFile(
                file=processed_stream,
                field_name='file',
                name=up_file.name,
                content_type=up_file.content_type,
                size=len(processed_file_bytes),
                charset=None
            )

            data = {
                'file': processed_uploaded_file,
                'title': up_file.name.split('.')[0],
                'description': request.data.get('description', ''),
                'doc_type': request.data.get('doc_type', 'other'),
                'should_compress': request.data.get('should_compress', False)
            }

            if 'title' not in data:
                data['title'] = up_file.name.split('.')[0]

            serializer = FileUploadSerializer(data=data, context={'request': request})

            if serializer.is_valid():
                uploaded_file = serializer.save()
                uploaded_files_data.append(UploadedFileSerializer(uploaded_file, context={'request': request}).data)

                processed_files.append({
                    'filename': f"{up_file.name}",
                    'content': base64.b64encode(processed_file_bytes).decode('utf-8'),
                    'content_type': up_file.content_type,
                })
            else:
                return Response({
                    'success': False,
                    'error': serializer.errors,
                    'action': 'multiple',
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'success': False,
                'error': {'file': f'Ошибка обработки: {str(e)}'}
            }, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'success': True,
        'message': 'Файлы успешно обработаны',
        'processed_files': processed_files,
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
def api_get_form(request, form_type='single'):
    """Получение формы для загрузки"""
    try:
        file_types = UploadedFile.types
        if form_type == 'multiple':
            template = 'core/multi_upload_form.html'
        elif form_type == 'single':
            template = 'core/single_upload_form.html'
        else:
            template = 'core/saved_form.html'

        form_html = render_to_string(template, {
            'csrf_token': request.META.get('CSRF_COOKIE'),
            'form_type': form_type,
            'file_types': file_types
        })

        return Response({
            'success': True,
            'form_html': form_html,
            'form_type': form_type,
            'file_types': file_types

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


def archive(request):
    """TODO: Дописать обработку авторизованного и не авторизованного пользователя"""
    return render(request, 'core/archive.html', {})


@csrf_exempt
@api_view(['GET'])
def api_get_archive_search_form(request):
    """TODO: Дописать обработку авторизованного и не авторизованного пользователя"""
    template = 'core/archive_search.html'
    users = User.objects.all().values('first_name', 'last_name')
    doc_types = UploadedFile.types

    search_form = render_to_string(template, {'csrf_token': request.META.get('CSRF_COOKIE'),
                                              'users': users, 'doc_types': doc_types})
    return Response({
        'success': True,
        'search_form': search_form,
        'users': users,
        'doc_types': doc_types
    })
