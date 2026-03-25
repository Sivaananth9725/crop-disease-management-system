from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AuthViewSet, DiseaseDetectionViewSet, AlertViewSet, 
    ChatbotViewSet, DashboardViewSet, WeatherViewSet, AdminViewSet
)

router = DefaultRouter()
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'detect', DiseaseDetectionViewSet, basename='detect')
router.register(r'alerts', AlertViewSet, basename='alerts')
router.register(r'chatbot', ChatbotViewSet, basename='chatbot')
router.register(r'dashboard', DashboardViewSet, basename='dashboard')
router.register(r'weather', WeatherViewSet, basename='weather')
router.register(r'admin', AdminViewSet, basename='admin')

urlpatterns = [
    path('', include(router.urls)),
]