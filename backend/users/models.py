from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    username = models.CharField(max_length=100, unique=True, blank=True, verbose_name='username (auto-generated)')
    email = models.EmailField(unique=True, db_index=True, error_messages={'unique': 'This email is already in use.'},
                              verbose_name='email address')
    surname = models.CharField(max_length=100, blank=True, null=True, verbose_name='surname')
    avatar = models.ImageField(upload_to='users/avatars/', blank=True, null=True, verbose_name='avatar')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
        ordering = ['created_at']


    def __str__(self):
        return f'{self.first_name}{self.last_name} - {self.email}({self.username})'


    def save(self, *args, **kwargs):

        if not self.username:
            base_username = f'user_{self.email.split('@')[0]}'

            username = base_username
            count = 1

            while CustomUser.objects.filter(username=base_username).exists():
                username = f'{base_username}_{count}'
                count += 1

            self.username = username

        super().save(*args, **kwargs)


