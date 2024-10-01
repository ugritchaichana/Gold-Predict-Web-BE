from django.db import models

class GoldPriceTH(models.Model):
    date = models.DateTimeField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    price_diff_unit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_diff_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.date} - {self.price}"
