from django.utils import timezone
import datetime


def expiry_date(days):
    return timezone.now() + datetime.timedelta(days=days)


def current_year():
    return datetime.datetime.now().year