from django.contrib import admin
from .models import User, DiseaseReport, Alert, ChatHistory

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'farm_size', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('username', 'email')

@admin.register(DiseaseReport)
class DiseaseReportAdmin(admin.ModelAdmin):
    list_display = ('disease_name', 'user', 'severity', 'confidence_score', 'created_at')
    list_filter = ('severity', 'created_at')
    search_fields = ('disease_name', 'user__username')

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('disease_report', 'affected_radius', 'created_at')
    list_filter = ('created_at',)

@admin.register(ChatHistory)
class ChatHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('question', 'user__username')