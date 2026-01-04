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
    title = request.POST.get('title', '')
    print(request.data)
    if not uploaded_file:
        return Response({
            'success': False,
            'error': {'file': 'Файл не выбран'}
        }, status=status.HTTP_400_BAD_REQUEST)

    content_type = uploaded_file.content_type

    file_bytes = uploaded_file.read()

    try:
        processed_file_bytes = miltiplicity_processing_excel(file_bytes)
        uploaded_file.seek(0)
    except Exception as e:
        return Response({
            'success': False,
            'error': {'file': f'Ошибка обработки: {str(e)}'}
        }, status=status.HTTP_400_BAD_REQUEST)

    processed_file_base64 = base64.b64encode(processed_file_bytes).decode('utf-8')

    serializer = FileUploadSerializer(
        data=request.data,
        context={'request': request}
    )

    if serializer.is_valid():
        uploaded_file = serializer.save()
    else:
        return Response({
            'success': False,
            'error': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'success': True,
        'message': 'Файл успешно обработан',
        'processed_file': {
            'filename': f"Обработанный_{title.lower()}",
            'content': processed_file_base64,
            'content_type': content_type,
        },
        'uploaded_file': UploadedFileSerializer(uploaded_file, context={'request': request}).data,
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def api_upload_multiple_files(request):
    """Загрузка нескольких файлов"""

    files_list = []
    for key in request.FILES:
        files_list.append(request.FILES[key])

    if not files_list:
        return Response({
            'success': False,
            'error': {'files': ['Файлы не выбраны']},
            'action': 'multiple',
        }, status=status.HTTP_400_BAD_REQUEST)

    serializer = MultiFileUploadSerializer(
        data=request.data,
        context={'request': request}
    )

    if serializer.is_valid():
        uploaded_files = serializer.save()

        response_serializer = UploadedFileSerializer(
            uploaded_files, many=True, context={'request': request}
        )
        return Response({
            'success': True,
            'message': f'Файлы успешно загружены: {len(uploaded_files)}',
            'files': response_serializer.data,
            'action': 'multiple',
        }, status=status.HTTP_201_CREATED)

    return Response({
        'success': False,
        'error': serializer.errors,
        'action': 'multiple',
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def api_get_form(request, form_type='single'):
    """Получение формы для загрузки"""
    try:
        print(form_type)
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
        print(form_html)

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
