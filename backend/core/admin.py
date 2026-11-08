from django.contrib import admin
from .models import UploadedFile


@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ('title', 'doc_type')
    list_filter = ('uploaded_by', 'title', 'doc_type')
    readonly_fields = ('uploaded_by', 'created_at')


    class Meta:
        model = UploadedFile
