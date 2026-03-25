from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.role == 'admin'

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.role == 'admin'

class IsFarmer(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.role == 'farmer'

class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        return obj.user == request.user