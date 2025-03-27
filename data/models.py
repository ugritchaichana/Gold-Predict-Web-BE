from django.db import models
from datetime import datetime
import pytz

def current_timestamp():
    return int(datetime.now().timestamp())

class USDTHB(models.Model):
    timestamp = models.IntegerField(default=current_timestamp)
    open = models.FloatField(default=0.0)
    close = models.FloatField(default=0.0)
    high = models.FloatField(default=0.0)
    low = models.FloatField(default=0.0)
    created_at = models.CharField(max_length=30, blank=True, editable=False)
    date = models.CharField(max_length=10, blank=True, editable=False)

class GoldTH(models.Model):
    timestamp = models.IntegerField(default=current_timestamp)
    price = models.FloatField(null=True, blank=True)
    bar_sell_price = models.FloatField(default=0.0)
    bar_price_change = models.FloatField(default=0.0)
    ornament_buy_price = models.FloatField(default=0.0)
    ornament_sell_price = models.FloatField(default=0.0)
    created_at = models.DateTimeField()
    created_time = models.CharField(max_length=10, blank=True, null=True)
    date = models.CharField(max_length=10, blank=True, null=True)