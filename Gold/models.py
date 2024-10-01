from django.db import models

class DailyGoldPrice(models.Model):
    date = models.DateTimeField()
    gold_price = models.FloatField()

class BackgroundTask(models.Model):
    id = models.AutoField(primary_key=True)
    task_name = models.CharField(max_length=255)
    run_at = models.DateTimeField()
    repeat = models.BooleanField()

    class Meta:
        db_table = 'background_task'
        managed = False