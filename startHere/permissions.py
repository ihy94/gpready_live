from subscription.models import Subscription
from rest_framework import permissions
from django.utils import timezone


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


class HasActivePackageSubscription(permissions.BasePermission):
    """Require an active, unexpired subscription for the selected package."""

    def has_permission(self, request, view):
        package_id = request.query_params.get('package', '')
        if not package_id.isdigit():
            return False
        view.package_id = int(package_id)
        return Subscription.objects.filter(
            user=request.user,
            package_id=view.package_id,
            active=True,
            expiry_date__gt=timezone.now(),
        ).exists()
