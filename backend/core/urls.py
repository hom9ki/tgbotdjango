from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('archive/', views.archive, name='archive'),

    path('api/files/', views.api_get_files, name='api_get_files'),
    path('api/files/html/', views.api_get_files_html, name='api_get_files_html'),
    path('api/files/archive/save/', views.api_file_save, name='api_file_save'),
    path('api/files/<int:file_id>/delete/', views.api_delete_file, name='api_delete_file'),
    path('api/files/<int:file_id>/download/', views.api_download_file, name='api_download_file'),
    path('api/upload/single/', views.api_upload_single_file, name='api_upload_single'),
    path('api/upload/multiple/', views.api_upload_multiple_files, name='api_upload_multiple'),
    path('api/form/<str:form_type>/', views.api_get_form, name='api_get_form'),
    path('api/form/', views.api_get_form, name='api_get_form_default'),
    path('api/archive/search/', views.api_search_files, name='api_search_files')

]
