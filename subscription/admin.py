from django.contrib import admin
from subscription.models import Package, PackagePlan, Subscription

admin.site.register(Package)
admin.site.register(PackagePlan)
admin.site.register(Subscription)