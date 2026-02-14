from rest_framework import serializers
from .models import CustomUser

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email']
        read_only_fields = ['id', 'username', 'email']

class LoginCustomUserSerializer(serializers.Serializer):
    class Meta:
        model = CustomUser
        fields = ['username', 'password']