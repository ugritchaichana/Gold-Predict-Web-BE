from django.db import models

class Gold_THB(models.Model):
    date = models.DateField()
    price = models.DecimalField(max_digits=12, decimal_places=4, null=True)
    open = models.DecimalField(max_digits=12, decimal_places=4, null=True)
    high = models.DecimalField(max_digits=12, decimal_places=4, null=True)
    low = models.DecimalField(max_digits=12, decimal_places=4, null=True)
    percent = models.DecimalField(max_digits=12, decimal_places=4, null=True)
    diff = models.DecimalField(max_digits=12, decimal_places=4, null=True)

    class Meta:
        db_table = 'gold_thb'


class Gold_USD(models.Model):
    date = models.DateField()
    price = models.DecimalField(max_digits=12, decimal_places=4)
    price_thb = models.DecimalField(max_digits=12, decimal_places=4)
    open = models.DecimalField(max_digits=12, decimal_places=4)
    high = models.DecimalField(max_digits=12, decimal_places=4)
    low = models.DecimalField(max_digits=12, decimal_places=4)
    percent = models.DecimalField(max_digits=12, decimal_places=4)
    diff = models.DecimalField(max_digits=12, decimal_places=4)

    class Meta:
        db_table = 'gold_usd'

class Gold_CNY(models.Model):
    date = models.DateField()
    price = models.DecimalField(max_digits=12, decimal_places=4)
    price_thb = models.DecimalField(max_digits=12, decimal_places=4)
    open = models.DecimalField(max_digits=12, decimal_places=4)
    high = models.DecimalField(max_digits=12, decimal_places=4)
    low = models.DecimalField(max_digits=12, decimal_places=4)
    percent = models.DecimalField(max_digits=12, decimal_places=4)
    diff = models.DecimalField(max_digits=12, decimal_places=4)

    class Meta:
        db_table = 'gold_cny'
