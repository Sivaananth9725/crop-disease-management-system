from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import DiseaseReport, Alert, ChatHistory

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'phone', 'latitude', 'longitude', 'farm_size']
        extra_kwargs = {'password': {'write_only': True}}
    
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class DiseaseReportSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = DiseaseReport
        fields = '__all__'
        read_only_fields = ['user', 'created_at']

class AlertSerializer(serializers.ModelSerializer):
    disease_report = DiseaseReportSerializer(read_only=True)
    
    class Meta:
        model = Alert
        fields = '__all__'