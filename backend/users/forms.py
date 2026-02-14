from django import forms
from .models import CustomUser, AllowedEmail
from django.contrib.auth import authenticate


class UserLoginForm(forms.Form):
    username = forms.CharField(label='Имя пользователя', help_text='Введите имя пользователя', required=True)
    password = forms.CharField(widget=forms.PasswordInput(), label='Пароль')

    class Meta:
        model = CustomUser
        fields = ['username', 'password']

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        if username and password:
            self.user_cache = authenticate(username=username, password=password)
            if self.user_cache is None:
                raise forms.ValidationError('Неверный логин или пароль')
            elif not self.user_cache.is_active:
                raise forms.ValidationError(
                    'Пользователь неактивен'
                )
        return cleaned_data

    def get_user(self):
        return self.user_cache


class UserRegistrationForm(forms.ModelForm):
    username = forms.CharField(label='Имя пользователя', help_text='Введите имя пользователя', required=True)
    password1 = forms.CharField(widget=forms.PasswordInput(), label='Введите пароль')
    password2 = forms.CharField(widget=forms.PasswordInput(), label='Повторите пароль')

    class Meta:
        model = CustomUser
        fields = ['username', 'password1', 'password2', 'email']
        labels = {
            'username': 'Имя пользователя',
            'email': 'Электронная почта',
            'password1': 'Пароль',
            'password2': 'Повторите пароль'
        }

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Пароли не совпадают')
        return password2

    def clean_password(self):
        password = self.cleaned_data.get('password1')
        if len(password) < 8:
            raise forms.ValidationError(
                'Пароль должен быть не менее 8 символов'
            )
        if not any(char.isdigit() for char in password):
            raise forms.ValidationError(
                'Пароль должен содержать хотя бы одну цифру'
            )
        if not any(char.isalpha() for char in password):
            raise forms.ValidationError(
                'Пароль должен содержать хотя бы одну букву'
            )
        return password

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError('Пользователь с такой почтой уже существует')
        if not AllowedEmail.objects.filter(email=email).exists():
            raise forms.ValidationError('Данный адрес электронной почты не разрешен для регистрации')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class UserChangePasswordForm(forms.Form):
    password_old = forms.CharField(widget=forms.PasswordInput(), label='Старый пароль')

    password_new1 = forms.CharField(widget=forms.PasswordInput(), label='Новый пароль')
    password_new2 = forms.CharField(widget=forms.PasswordInput(), label='Повторите новый пароль')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_password_new2(self):
        password_new2 = self.cleaned_data.get('password_new2')
        password_new1 = self.cleaned_data.get('password_new1')
        if password_new1 and password_new2 and password_new1 != password_new2:
            raise forms.ValidationError('Пароли не совпадают')
        return password_new2

    def clean_password_new1(self):
        password_new1 = self.cleaned_data.get('password_new1')
        if len(password_new1) < 8:
            raise forms.ValidationError(
                'Пароль должен быть не менее 8 символов'
            )
        if not any(char.isdigit() for char in password_new1):
            raise forms.ValidationError(
                'Пароль должен содержать хотя бы одну цифру'
            )
        if not any(char.isalpha() for char in password_new1):
            raise forms.ValidationError(
                'Пароль должен содержать хотя бы одну букву')
        return password_new1

    def clean(self):
        cleaned_data = super().clean()
        old_password = cleaned_data.get('password_old')
        if old_password:
            user = authenticate(username=self.user.username, password=old_password)
            if user is None:
                raise forms.ValidationError('Неверный пароль')
        return cleaned_data

    def save(self, commit=True):
        self.user.set_password(self.cleaned_data['password_new1'])
        if commit:
            self.user.save()
        return self.user
