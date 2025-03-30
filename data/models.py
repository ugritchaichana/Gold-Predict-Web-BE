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
    price = models.FloatField(null=True, blank=True, default=0.0)
    bar_sell_price = models.FloatField(null=True, blank=True, default=0.0)
    bar_price_change = models.FloatField(null=True, blank=True, default=0.0)
    ornament_buy_price = models.FloatField(null=True, blank=True, default=0.0)
    ornament_sell_price = models.FloatField(null=True, blank=True, default=0.0)
    created_time = models.CharField(max_length=10, blank=True, null=True)
    created_at = models.DateTimeField(null=True, blank=True, default=None)
    date = models.CharField(max_length=10, blank=True, null=True)

class GoldUS(models.Model):
    timestamp = models.IntegerField(default=current_timestamp)
    price = models.FloatField(null=True, blank=True, default=0.0)
    close_price = models.FloatField(null=True, blank=True, default=0.0)
    high_price = models.FloatField(null=True, blank=True, default=0.0)
    low_price = models.FloatField(null=True, blank=True, default=0.0)
    volume = models.FloatField(null=True, blank=True, default=0.0)
    volume_weight_avg = models.FloatField(null=True, blank=True, default=0.0)
    num_transactions = models.FloatField(null=True, blank=True, default=0.0)
    created_at = models.DateTimeField(null=True, blank=True, default=None)
    date = models.CharField(max_length=10, blank=True, null=True)