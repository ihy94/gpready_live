from rest_framework.views import APIView
from django.core.mail import EmailMessage, get_connection
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from core.models import User
import random
import string

from djoser import serializers

def generate_random_password(length=8):
    characters = string.ascii_letters + string.digits
    random_password = ''.join(random.choice(characters) for _ in range(length))
    return random_password


class SendEmail(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        try: 
            user = User.objects.get(email=request.data.get("email"))
            newPass = generate_random_password()
            user.set_password(newPass)
            user.save()
            with get_connection(  
                host=settings.EMAIL_HOST, 
                port=settings.EMAIL_PORT,  
                username=settings.EMAIL_HOST_USER, 
                password=settings.EMAIL_HOST_PASSWORD, 
                use_tls=settings.EMAIL_USE_TLS  
            ) as connection: 
                subject = "Your new password for gpready account" 
                email_from = settings.EMAIL_HOST_USER  
                recipient_list = [request.data.get("email")]  
                message = f"your new password is : {newPass}"
                EmailMessage(subject, message, email_from, recipient_list, connection=connection).send()
            return Response({ "msg" : "New password has been sent to your email" }, status=status.HTTP_200_OK) 

        except User.DoesNotExist:
            return Response({
                "msg" : "You don't have active account with this email"
            },
            status=status.HTTP_400_BAD_REQUEST
        )