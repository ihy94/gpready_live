from django.urls import path
from rest_framework_nested import routers
from . import views


router = routers.DefaultRouter()

router.register('subscriptions', views.SubscriptionViewSet, basename='subscriptions')

router.register('packages', views.PackageViewset, basename='packages')


# URLConf
urlpatterns = [
    path('create-checkout-session/', views.CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
    path('webhooks/stripe/', views.stripe_webhook, name='stripe-webhook'),
] + router.urls