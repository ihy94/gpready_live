from rest_framework import serializers
from subscription.models import Package, PackagePlan, Subscription



class PackagePlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackagePlan
        fields = ['id', 'price', 'plan_duration']

class PackageSerializer(serializers.ModelSerializer):
    plans = PackagePlanSerializer(many=True)
    class Meta:
        model = Package
        fields = ['id', 'title', 'description','plans']


class SubscriptionSerializer(serializers.ModelSerializer):
    package = PackageSerializer()
    class Meta:
        model = Subscription
        fields = ['id', 'package', 'expiry_date', 'active']