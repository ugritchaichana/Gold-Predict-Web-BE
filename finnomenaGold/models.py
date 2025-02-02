from django.db import models
from datetime import datetime
import time

class Gold_US(models.Model):
    timestamp = models.BigIntegerField(unique=True,null=True)
    price = models.FloatField(null=True)
    close_price = models.FloatField(null=True)
    high_price = models.FloatField(null=True)
    low_price = models.FloatField(null=True)
    volume = models.FloatField(null=True)
    volume_weight_avg = models.FloatField(null=True)
    num_transactions = models.IntegerField(null=True)
    date = models.CharField(max_length=16,null=True)
    created_at = models.DateTimeField(null=True)

    def __str__(self):
        return f"Gold_US {self.timestamp}"

class Gold_TH(models.Model):
    created_at = models.DateTimeField()
    created_time = models.CharField(max_length=10, blank=True, null=True)
    price = models.FloatField(null=True, blank=True)
    bar_sell_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    bar_price_change = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    ornament_buy_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    ornament_sell_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    timestamp = models.BigIntegerField(blank=True, null=True)
    date = models.CharField(max_length=16, blank=True, null=True)

    def __str__(self):
        return f"{self.created_at} - {self.price}"

    def save(self, *args, **kwargs):
        if self.created_at:
            self.date = self.created_at.strftime('%d-%m-%y')
        elif not self.date:
            self.date = datetime.now().strftime('%d-%m-%y')
        super().save(*args, **kwargs)