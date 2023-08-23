from django.urls import path
from . import views


urlpatterns = [
    path('request_new_password/', views.SendEmail.as_view()),
]