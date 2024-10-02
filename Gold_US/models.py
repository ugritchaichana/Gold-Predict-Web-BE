from django.db import models

class GoldPriceUS(models.Model):
    date = models.DateField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default='0')
    open = models.DecimalField(max_digits=10, decimal_places=2, default='0')
    high = models.DecimalField(max_digits=10, decimal_places=2, default='0')
    low = models.DecimalField(max_digits=10, decimal_places=2, default='0')
    volume = models.DecimalField(max_digits=15, decimal_places=2, default='0')
    percent = models.DecimalField(max_digits=5, decimal_places=2, default='0')
    unitUSD = models.CharField(max_length=10, default='0')
    unitTHB = models.CharField(max_length=10, default='0')

    def __str__(self):
        return f"{self.date} - {self.price}"
