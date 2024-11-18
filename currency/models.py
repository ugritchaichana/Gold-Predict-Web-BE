from django.db import models

class USDTHB(models.Model):
    date = models.DateField(db_index=True)
    price = models.FloatField()
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    percent = models.FloatField()
    diff = models.FloatField()

    class Meta:
        db_table = 'usdthb'

class CNYTHB(models.Model):
    date = models.DateField(db_index=True)
    price = models.FloatField()
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    percent = models.FloatField()
    diff = models.FloatField()

    class Meta:
        db_table = 'cnythb'
