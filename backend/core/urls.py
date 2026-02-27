from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('archive/', views.archive, name='archive'),

    path('api/files/archive/save/', views.api_file_save, name='api_file_save'),
    path('api/files/<int:file_id>/delete/', views.api_delete_file, name='api_delete_file'),
    path('api/files/<int:file_id>/download/', views.api_download_file, name='api_download_file'),
    path('api/upload/single/', views.api_upload_single_file, name='api_upload_single'),
    path('api/upload/multiple/', views.api_upload_multiple_files, name='api_upload_multiple'),
    path('api/upload/goodsmove/', views.api_upload_file_return_original, name='api_upload_file_return_original'),
    path('api/form/<str:form_type>/', views.api_get_form, name='api_get_form'),
    path('api/form/', views.api_get_form, name='api_get_form_default'),
    path('api/archive/search/', views.api_search_files, name='api_search_files'),

    path('api/task/<str:task_id>/result/', views.api_get_task_result, name='api_get_task_result'),
    path('api/celery/upload/', views.api_processing_files_using_celery, name='api_processing_files_using_celery'),

]
