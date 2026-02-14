from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    username = models.CharField(max_length=100, unique=True, verbose_name='username (auto-generated)')
    email = models.EmailField(unique=True, verbose_name='email address')
    first_name = models.CharField(max_length=100, verbose_name='first name')
    last_name = models.CharField(max_length=100, verbose_name='last name')
    surname = models.CharField(max_length=100, verbose_name='surname')
    avatar = models.ImageField(upload_to='users/avatars/', blank=True, null=True, verbose_name='avatar')

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def __str__(self):
        return f'{self.first_name}{self.last_name} - {self.email}({self.username})'

    def create_full_name(self, save=True):
        try:
            allowed_email = AllowedEmail.objects.get(email=self.email)
            print(f'create_full_name: {allowed_email.first_name, allowed_email.last_name, allowed_email.surname}')
            self.first_name = allowed_email.first_name
            self.last_name = allowed_email.last_name
            self.surname = allowed_email.surname
            if save:
                self.save()
        except AllowedEmail.DoesNotExist:
            pass

    def save(self, *args, **kwargs):
        if self.first_name == '' or self.last_name == '' or self.surname == '':
            self.create_full_name(save=False)
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        if self.surname:
            return f'{self.last_name} {self.first_name} {self.surname}'
        else:
            return f'{self.last_name} {self.first_name}'


class AllowedEmail(models.Model):
    email = models.EmailField(unique=True, db_index=True, verbose_name='email address')
    first_name = models.CharField(max_length=100, default='', verbose_name='first name')
    last_name = models.CharField(max_length=100, default='', verbose_name='last name')
    surname = models.CharField(max_length=100, default='', verbose_name='surname')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='created at')

    class Meta:
        verbose_name = 'allowed email'
        verbose_name_plural = 'allowed emails'

    def __str__(self):
        return self.email
