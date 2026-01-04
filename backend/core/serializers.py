import time

from rest_framework import serializers
import os
from .models import UploadedFile
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']
        read_only_fields = ['id', 'username', 'email']


class UploadedFileSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)
    download_url = serializers.SerializerMethodField()
    filename = serializers.SerializerMethodField()
    filesize = serializers.SerializerMethodField()
    readable_size = serializers.CharField(source='readable_filesize', read_only=True)
    file_extension = serializers.SerializerMethodField()

    class Meta:
        model = UploadedFile
        fields = [
            'id', 'description', 'title', 'doc_type', 'uploaded_by', 'file',
            'download_url', 'filename', 'filesize', 'readable_size',
            'file_extension', 'created_at',
        ]
        read_only_fields = ['created_at', 'uploaded_by']

    def get_download_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None

    def get_filename(self, obj):
        return obj.filename

    def get_filesize(self, obj):
        return obj.filesize

    def get_file_extension(self, obj):
        return obj.file_extension


class FileUploadSerializer(serializers.ModelSerializer):
    should_compress = serializers.BooleanField(default=False, required=False)

    class Meta:
        model = UploadedFile
        fields = ['file', 'title', 'doc_type', 'description', 'should_compress']
        extra_kwargs = {
            'title': {'required': False, 'allow_blank': True},
            'description': {'required': True, 'allow_blank': True}
        }

    def validate_file(self, value):
        max_size = 50 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError(
                'Файл не должен превышать 10 МБ.'
            )

        allowed_extensions = ['.xlsx', '.xls', '.csv']

        ext = os.path.splitext(value.name)[1].lower()
        if ext not in allowed_extensions:
            raise serializers.ValidationError(
                f'Файл должен быть одним из следующих типов: {", ".join(allowed_extensions)}'
            )
        return value

    def create(self, validated_data):

        should_compress = validated_data.pop('should_compress', False)

        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['uploaded_by'] = request.user
        else:
            validated_data['uploaded_by'] = None

        if should_compress:
            print('Compressing file...')
            time.sleep(5)

        return super().create(validated_data)


class MultiFileUploadSerializer(serializers.Serializer):
    files = serializers.ListField(
        child=serializers.FileField(), write_only=True
    )
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    should_compress = serializers.BooleanField(default=False, required=False)

    def validate_files(self, files):
        if not files:
            raise serializers.ValidationError(
                'Выберите хотя бы один файл.'
            )

        max_size = 50 * 1024 * 1024
        allowed_extensions = ['.xlsx', '.xls', '.csv']

        for file in files:
            if file.size > max_size:
                raise serializers.ValidationError(
                    f'Файл {file.name} не должен превышать 10 МБ.'
                )
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in allowed_extensions:
                raise serializers.ValidationError(
                    f'Файл должен быть одним из следующих типов: {", ".join(allowed_extensions)}'
                )
        return files

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            user = request.user
        else:
            user = None

        files = validated_data['files']
        description = validated_data.get('description')

        uploaded_files = []

        for file in files:
            filename = os.path.splitext(file.name)[0]

            uploaded_file = UploadedFile.objects.create(
                file=file, title=filename, description=description,
                uploaded_by=user
            )
            uploaded_file.save()
            uploaded_files.append(uploaded_file)

        return uploaded_files
