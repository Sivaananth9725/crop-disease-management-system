from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    ROLE_CHOICES = (
        ('farmer', 'Farmer'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='farmer')
    phone = models.CharField(max_length=15, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    farm_size = models.FloatField(null=True, blank=True)  # in acres
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.username

class DiseaseReport(models.Model):
    SEVERITY_CHOICES = (
        ('low', 'Low - Monitor Only'),
        ('medium', 'Medium - Treat Soon'),
        ('high', 'High - Immediate Action Required'),
        ('critical', 'Critical - Emergency Alert')
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    image = models.ImageField(upload_to='disease_images/')
    disease_name = models.CharField(max_length=200)
    confidence_score = models.FloatField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    
    # Environmental data
    temperature = models.FloatField()
    humidity = models.FloatField()
    soil_ph = models.FloatField(default=6.5)
    
    # Recommendations
    treatment = models.TextField()
    prevention = models.TextField()
    risk_level = models.CharField(max_length=20)
    
    location_lat = models.FloatField()
    location_lon = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.disease_name} - {self.user.username} - {self.created_at}"

class Alert(models.Model):
    disease_report = models.ForeignKey(DiseaseReport, on_delete=models.CASCADE)
    message = models.TextField()
    affected_radius = models.IntegerField(default=5)  # in km
    notified_users = models.ManyToManyField(User, related_name='alerts')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Alert for {self.disease_report.disease_name} - {self.created_at}"

class ChatHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.TextField()
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)