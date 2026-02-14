from django.urls import path

from . import views

urlpatterns = [
    path('account/login/', views.user_login, name='login'),
    path('account/logout/', views.user_logout, name='logout'),
    path('account/register/', views.user_register, name='registration'),
]
