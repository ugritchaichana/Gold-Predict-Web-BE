from django.db import models

class Log(models.Model):
    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100)
    message = models.TextField()
    status = models.CharField(max_length=20)

    class Meta:
        db_table = 'logs'
        verbose_name = 'Log Entry'
        verbose_name_plural = 'Log Entries'
