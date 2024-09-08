from django.db import models

class GoldPrice(models.Model):
    date = models.DateField()
    gold_price = models.DecimalField(max_digits=10, decimal_places=2)
