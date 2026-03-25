import requests
import json
from django.conf import settings

class NotificationService:
    def __init__(self):
        self.fcm_url = "https://fcm.googleapis.com/fcm/send"
        self.server_key = getattr(settings, 'FCM_SERVER_KEY', None)
    
    def send_push_notification(self, user, title, message, data=None):
        """Send push notification to a specific user"""
        try:
            if not hasattr(user, 'fcm_token') or not user.fcm_token:
                return False
            
            payload = {
                'to': user.fcm_token,
                'notification': {
                    'title': title,
                    'body': message,
                    'sound': 'default'
                },
                'data': data or {}
            }
            
            headers = {
                'Authorization': f'key={self.server_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(self.fcm_url, json=payload, headers=headers)
            return response.status_code == 200
        except Exception as e:
            print(f"Error sending push notification: {e}")
            return False
    
    def send_sms(self, phone_number, message):
        """Send SMS notification (optional integration with Twilio)"""
        pass
    
    def send_email(self, email, subject, message):
        """Send email notification"""
        pass

notification_service = NotificationService()