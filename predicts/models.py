from django.db import models

# Create your models here.
class Week(models.Model):
    timestamp = models.BigIntegerField(unique=True,null=True)
    price_0 = models.FloatField(null=True)
    price_1 = models.FloatField(null=True)
    price_2 = models.FloatField(null=True)
    price_3 = models.FloatField(null=True)
    price_4 = models.FloatField(null=True)
    price_5 = models.FloatField(null=True)
    price_6 = models.FloatField(null=True)
    price_7 = models.FloatField(null=True)
    date_1  = models.CharField(max_length=16,null=True)
    date_2 = models.CharField(max_length=16,null=True)
    date_3 = models.CharField(max_length=16,null=True)
    date_4 = models.CharField(max_length=16,null=True)
    date_5 = models.CharField(max_length=16,null=True)
    date_6 = models.CharField(max_length=16,null=True)
    date_7 = models.CharField(max_length=16,null=True)
    date = models.CharField(max_length=16,null=True)
    created_at = models.DateTimeField(null=True)

class Month(models.Model):
    timestamp = models.BigIntegerField(unique=True,null=True)
    open = models.FloatField(null=True)
    high = models.FloatField(null=True)
    low = models.FloatField(null=True)
    date = models.CharField(max_length=16,null=True)
    created_at = models.DateTimeField(null=True)
    month_predict = models.CharField(max_length=16,null=True)