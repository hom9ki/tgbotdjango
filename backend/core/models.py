from django.db import models
import os


class UploadedFile(models.Model):
    types = (
        ('matrix', 'Матрица'),
        ('nomenclature', 'Номенклатура'),
        ('price', 'Цены'),
        ('other', 'Другое'),
    )

    uploaded_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True,
                                    verbose_name='Пользователь')
    file = models.FileField(upload_to='uploads/', verbose_name='Файл')
    title = models.CharField(max_length=100, blank=True, null=True, verbose_name='Имя файла')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    doc_type = models.CharField(choices=types, default='other', max_length=100, verbose_name='Тип документа')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата загрузки')

    def __str__(self):
        return self.title or self.file.name

    class Meta:
        verbose_name = 'Загруженный файл'
        verbose_name_plural = 'Загруженные файлы'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.title and self.file:
            filename = os.path.splitext(self.file.name)[0]
            self.title = filename
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        super().delete(*args, **kwargs)

    @property
    def filename(self):
        return os.path.basename(self.file.name) if self.file else ''

    @property
    def filesize(self):
        if self.file:
            return self.file.size
        else:
            return 0

    @property
    def readable_filesize(self):
        size = self.filesize
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"

    @property
    def file_extension(self):
        if self.file:
            return os.path.splitext(self.file.name)[1]
        else:
            return ''
