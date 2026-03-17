import os

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.utils import OperationalError
import os

User = get_user_model()


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Инициализация суперпользователя...'))

        self.create_superuser()

        self.stdout.write(self.style.SUCCESS('Суперпользователь создан.'))

    def create_superuser(self):
        self.stdout.write(self.style.SUCCESS('Создание суперпользователя...'))

        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        first_name = os.environ.get('DJANGO_SUPERUSER_FIRST_NAME', 'Admin')
        last_name = os.environ.get('DJANGO_SUPERUSER_LAST_NAME', 'User')
        surname = os.environ.get('DJANGO_SUPERUSER_SURNAME', '')

        if not all([username, email, password]):
            self.stdout.write(self.style.ERROR(f'Не указаны обязательные параметры{[username, email, password]}.'))
            return
        try:
            if not User.objects.filter(email=email).exists():
                User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    surname=surname
                )
                self.stdout.write(self.style.SUCCESS(f'Суперпользователь {username} создан.'))
            else:
                self.stdout.write(self.style.WARNING(f'Суперпользователь {username} уже существует.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка при создании суперпользователя: {e}'))
