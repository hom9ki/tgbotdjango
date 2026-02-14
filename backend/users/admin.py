from django.contrib import admin
from .models import CustomUser, AllowedEmail


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name')
    list_display_links = ('username',)
    search_fields = ('first_name', 'last_name', 'email', 'username')
    search_help_text = 'Поиск по имени, фамилии, email, логину'
    empty_value_display = '-----'


@admin.register(AllowedEmail)
class AllowedEmailAdmin(admin.ModelAdmin):
    list_display = ('email', 'created_at')
    list_display_links = ('email',)
    search_fields = ('email',)
    search_help_text = 'Поиск по email'
