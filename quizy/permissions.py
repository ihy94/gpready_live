from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS
from subscription.models import Subscription


class hasActiveSubscription(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if user.subscriptions.filter(active=True).exists():
            return True
        else:
            return False




class IsSubcribed(permissions.BasePermission):
    def has_permission(self, request, view):
        subscription = request.query_params.get('subscription')

        if request.method in SAFE_METHODS:
            if subscription:
                is_subscribed = Subscription.objects.filter(id=subscription, active=True).exists()
                return is_subscribed
            
            elif view.action == 'retrieve':
                return True
            
            else:
                return False
            
        else:
            return Subscription.objects.filter(user_id=request.user.id, active=True).exists()
        
    
    def has_object_permission(self, request, view, obj):
        if view.action == 'retrieve':
            return obj.subscription.active