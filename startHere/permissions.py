from subscription.models import Subscription
from rest_framework import permissions


class hasActiveSubscription(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if user.subscriptions.filter(active=True).exists():
            return True
        else:
            return False



class IsSubcribed(permissions.BasePermission):
    def has_permission(self, request, view):
        package = request.query_params.get('package')

        if package:
            is_subscribed = Subscription.objects.filter(user_id=request.user.id, package_id=package, active=True).exists()
            return is_subscribed
        return Subscription.objects.filter(user_id=request.user.id, active=True).exists()