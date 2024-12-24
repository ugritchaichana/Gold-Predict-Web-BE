from django.db import models

class Gold_US(models.Model):
    created_at = models.DateTimeField()
    created_time = models.CharField(max_length=10, blank=True, null=True)
    bar_buy_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    bar_sell_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    bar_price_change = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    ornament_buy_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    ornament_sell_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    timestamp = models.BigIntegerField(blank=True, null=True)
    created_date_time = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.created_at} - {self.bar_buy_price}"

class Gold_TH(models.Model):
    created_at = models.DateTimeField()
    created_time = models.CharField(max_length=10, blank=True, null=True)
    bar_buy_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    bar_sell_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    bar_price_change = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    ornament_buy_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    ornament_sell_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    timestamp = models.BigIntegerField(blank=True, null=True)
    created_date_time = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.created_at} - {self.bar_buy_price}"