from rest_framework import permissions

class hasActiveSubscription(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if user.subscriptions.filter(active=True).exists():
            return True
        else:
            return False