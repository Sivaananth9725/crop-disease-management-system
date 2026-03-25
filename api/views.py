from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from .models import DiseaseReport, Alert, ChatHistory
from .serializers import UserSerializer, DiseaseReportSerializer, AlertSerializer
from rest_framework_simplejwt.tokens import RefreshToken
import io
import os

User = get_user_model()

class AuthViewSet(viewsets.GenericViewSet):
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Create default admin if this is first user
            if User.objects.count() == 1:
                admin_user = User.objects.create_superuser(
                    username='admin',
                    email='admin@example.com',
                    password='admin123',
                    role='admin'
                )
            
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': serializer.data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        user = User.objects.filter(username=username).first()
        if user and user.check_password(password):
            refresh = RefreshToken.for_user(user)
            serializer = UserSerializer(user)
            return Response({
                'user': serializer.data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    
    @action(detail=False, methods=['post'])
    def refresh(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'error': 'Refresh token required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            refresh = RefreshToken(refresh_token)
            return Response({'access': str(refresh.access_token)})
        except:
            return Response({'error': 'Invalid refresh token'}, status=status.HTTP_401_UNAUTHORIZED)

class DiseaseDetectionViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def detect(self, request):
        # Import services inside method to avoid circular imports
        from ml_model.model import classifier
        from weather.weather_service import weather_service
        from alerts.geospatial import geospatial_service
        
        try:
            # Get uploaded image
            image_file = request.FILES.get('image')
            if not image_file:
                return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)

            image_bytes = image_file.read()
            if not image_bytes:
                return Response({'error': 'Image data is empty'}, status=status.HTTP_400_BAD_REQUEST)

            if hasattr(image_file, 'seek'):
                image_file.seek(0)

            # Get location data
            latitude = request.data.get('latitude')
            longitude = request.data.get('longitude')
            soil_ph = request.data.get('soil_ph', 6.5)
            
            if not latitude or not longitude:
                return Response({'error': 'Location data required'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Get weather data
            weather_data = weather_service.get_weather(float(latitude), float(longitude))
            
            # Predict disease
            try:
                prediction = classifier.predict(io.BytesIO(image_bytes), weather_data, float(soil_ph))
            except Exception as exc:
                return Response({'error': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Save disease report
            disease_report = DiseaseReport.objects.create(
                user=request.user,
                image=image_file,
                disease_name=prediction['disease_name'],
                confidence_score=prediction['confidence'] / 100,
                severity=prediction['severity'],
                temperature=weather_data['temperature'],
                humidity=weather_data['humidity'],
                soil_ph=soil_ph,
                treatment=prediction['treatment'],
                prevention=prediction['prevention'],
                risk_level=prediction['risk_level'],
                location_lat=float(latitude),
                location_lon=float(longitude)
            )
            
            # Create alert if severity is high or critical
            alert_created = False
            alert_message = None
            if prediction['severity'] in ['high', 'critical']:
                alert = geospatial_service.create_alert_for_disease(disease_report, radius_km=5)
                if alert:
                    alert_created = True
                    alert_message = alert.message
            
            serializer = DiseaseReportSerializer(disease_report)
            prediction['report_id'] = disease_report.id
            prediction['weather_data'] = weather_data
            prediction['alert_created'] = alert_created
            prediction['alert_message'] = alert_message
            
            return Response(prediction, status=status.HTTP_200_OK)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        reports = DiseaseReport.objects.filter(user=request.user).order_by('-created_at')
        serializer = DiseaseReportSerializer(reports, many=True)
        return Response(serializer.data)

class AlertViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AlertSerializer
    
    def get_queryset(self):
        return Alert.objects.filter(notified_users=self.request.user).order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        count = Alert.objects.filter(notified_users=request.user).count()
        return Response({'unread_count': count})
    
    @action(detail=False, methods=['post'])
    def mark_read(self, request):
        alert_id = request.data.get('alert_id')
        if alert_id:
            alert = get_object_or_404(Alert, id=alert_id, notified_users=request.user)
            alert.delete()  # Remove alert after reading
            return Response({'success': True})
        return Response({'error': 'Alert ID required'}, status=status.HTTP_400_BAD_REQUEST)

class ChatbotViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def ask(self, request):
        # Import chatbot service inside method
        from chatbot.groq_service import chatbot_service
        
        question = request.data.get('question')
        if not question:
            return Response({'error': 'No question provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get context from user's farm data
        context = f"Farmer with farm size: {request.user.farm_size} acres" if request.user.farm_size else None
        
        # Get response from chatbot
        answer = chatbot_service.get_response(question, context)
        
        # Save chat history
        ChatHistory.objects.create(
            user=request.user,
            question=question,
            answer=answer
        )
        
        return Response({
            'question': question,
            'answer': answer
        })
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        chats = ChatHistory.objects.filter(user=request.user).order_by('-created_at')[:50]
        return Response([{
            'question': chat.question,
            'answer': chat.answer,
            'created_at': chat.created_at
        } for chat in chats])

class DashboardViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        reports = DiseaseReport.objects.filter(user=request.user)
        
        stats = {
            'total_detections': reports.count(),
            'high_risk_detections': reports.filter(risk_level='High').count(),
            'critical_detections': reports.filter(severity='critical').count(),
            'low_risk_count': reports.filter(severity='low').count(),
            'medium_risk_count': reports.filter(severity='medium').count(),
            'high_risk_count': reports.filter(severity='high').count(),
            'critical_count': reports.filter(severity='critical').count(),
            'recent_detections': DiseaseReportSerializer(reports.order_by('-created_at')[:5], many=True).data,
            'alerts': AlertSerializer(Alert.objects.filter(notified_users=request.user)[:10], many=True).data
        }
        
        return Response(stats)

class WeatherViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        # Import weather service inside method
        from weather.weather_service import weather_service
        
        lat = request.query_params.get('lat')
        lon = request.query_params.get('lon')
        
        if not lat or not lon:
            return Response({'error': 'Latitude and longitude required'}, status=status.HTTP_400_BAD_REQUEST)
        
        weather_data = weather_service.get_weather(float(lat), float(lon))
        return Response(weather_data)

class AdminViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['users', 'reports', 'stats', 'add_admin', 'delete_report']:
            return [IsAuthenticated()]
        return super().get_permissions()
    
    @action(detail=False, methods=['get'])
    def users(self, request):
        if request.user.role != 'admin':
            return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
        
        users = User.objects.all().order_by('-date_joined')
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def reports(self, request):
        if request.user.role != 'admin':
            return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
        
        reports = DiseaseReport.objects.all().order_by('-created_at')
        serializer = DiseaseReportSerializer(reports, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        if request.user.role != 'admin':
            return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
        
        stats = {
            'total_users': User.objects.count(),
            'total_reports': DiseaseReport.objects.count(),
            'active_alerts': Alert.objects.count(),
            'high_risk_cases': DiseaseReport.objects.filter(severity='high').count()
        }
        return Response(stats)
    
    @action(detail=False, methods=['post'])
    def add_admin(self, request):
        if request.user.role != 'admin':
            return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
        
        username = request.data.get('username')
        email = request.data.get('email')
        
        if not username or not email:
            return Response({'error': 'Username and email required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate random password
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for i in range(10))
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role='admin'
        )
        
        return Response({
            'message': 'Admin created successfully',
            'username': username,
            'password': password
        })
    
    @action(detail=False, methods=['delete'])
    def delete_report(self, request):
        if request.user.role != 'admin':
            return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
        
        report_id = request.data.get('report_id')
        if report_id:
            report = get_object_or_404(DiseaseReport, id=report_id)
            report.delete()
            return Response({'success': True})
        return Response({'error': 'Report ID required'}, status=status.HTTP_400_BAD_REQUEST)