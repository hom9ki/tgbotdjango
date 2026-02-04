from django.contrib import admin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email')
    list_display_links = ('email', 'last_name')
    search_fields = ('first_name', 'last_name', 'email', 'username')
    search_help_text = 'Поиск по имени, фамилии, email, логину'
    empty_value_display = '-----'
