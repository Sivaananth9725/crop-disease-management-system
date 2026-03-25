import math

class GeospatialAlertService:
    def __init__(self):
        self.earth_radius = 6371  # km
    
    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points using Haversine formula"""
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return self.earth_radius * c
    
    def get_user_model(self):
        """Get user model lazily"""
        from django.contrib.auth import get_user_model
        return get_user_model()
    
    def get_alert_model(self):
        """Get alert model lazily"""
        from api.models import Alert
        return Alert
    
    def get_nearby_farmers(self, center_lat, center_lon, radius_km=5):
        """Get all farmers within radius of center point"""
        try:
            User = self.get_user_model()
            all_farmers = User.objects.filter(role='farmer', latitude__isnull=False, longitude__isnull=False)
            nearby_farmers = []
            
            for farmer in all_farmers:
                if farmer.latitude and farmer.longitude:
                    distance = self.haversine_distance(center_lat, center_lon, farmer.latitude, farmer.longitude)
                    if distance <= radius_km:
                        nearby_farmers.append({
                            'user': farmer,
                            'distance': distance
                        })
            
            return nearby_farmers
        except Exception as e:
            print(f"Error getting nearby farmers: {e}")
            return []
    
    def create_alert_for_disease(self, disease_report, radius_km=5):
        """Create and send alerts to nearby farmers"""
        try:
            Alert = self.get_alert_model()
            
            # Get nearby farmers
            nearby_farmers = self.get_nearby_farmers(
                disease_report.location_lat,
                disease_report.location_lon,
                radius_km
            )
            
            if not nearby_farmers:
                return None
            
            # Create alert message
            alert_message = f"""🚨 DISEASE ALERT 🚨

Disease: {disease_report.disease_name}
Severity: {disease_report.severity.upper()}
Location: Within {radius_km}km of your area

Recommended Action: {disease_report.treatment[:200]}

Please inspect your crops immediately."""
            
            # Create alert record
            alert = Alert.objects.create(
                disease_report=disease_report,
                message=alert_message,
                affected_radius=radius_km
            )
            
            # Add notified users
            farmer_users = [farmer['user'] for farmer in nearby_farmers]
            alert.notified_users.add(*farmer_users)
            
            return alert
        except Exception as e:
            print(f"Error creating alert: {e}")
            return None

geospatial_service = GeospatialAlertService()