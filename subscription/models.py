from django.db import models
from django.conf import settings
from django.utils.timezone import now, timedelta


# Create your models here.
class Package(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()

   
    def __str__(self):
        return str(self.title)

class PackagePlan(models.Model):
    DURATION = [
        (3, '3 months'),
        (6, '6 months'),
        (9, '9 months'),
        (12, '12 month'),
    ]
    package = models.ManyToManyField(Package, related_name='plans')
    plan_duration = models.PositiveIntegerField(
                        choices=DURATION,
                        default=3)  
    price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f'{self.plan_duration} months {self.price}'
    
class Subscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscriptions')
    package = models.ForeignKey(Package, on_delete=models.CASCADE) 
    active = models.BooleanField(default=True)
    start_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateTimeField(default=now)


    def set_expiry_date(self, duration):
        self.expiry_date = now() + timedelta(days=30 * duration)

    
    def has_expired(self):
        return now() >= self.expiry_date


    class Meta:
        unique_together = ('user','package',)



        



