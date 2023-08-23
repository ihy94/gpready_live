from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from djoser.serializers import UserSerializer as BaseUserSerializer 
from rest_framework import serializers


class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        fields = ['id','username','password','email']



class UserSerializer(BaseUserSerializer):
    has_active_subscription = serializers.SerializerMethodField(method_name='get_has_active_subscription')
    class Meta(BaseUserSerializer.Meta):
        fields = ['id', 'username', 'email', 'has_active_subscription']
        

    def get_has_active_subscription(self, user):
        if user.subscriptions.filter(active=True).exists():
            return True
        else:
            return False
                


        
