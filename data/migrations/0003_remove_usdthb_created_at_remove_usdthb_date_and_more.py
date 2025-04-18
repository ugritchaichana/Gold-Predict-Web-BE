# Generated by Django 5.1.1 on 2025-03-21 17:06

import data.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0002_remove_usdthb_created_time'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='usdthb',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='usdthb',
            name='date',
        ),
        migrations.AlterField(
            model_name='usdthb',
            name='close',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='usdthb',
            name='high',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='usdthb',
            name='low',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='usdthb',
            name='open',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='usdthb',
            name='timestamp',
            field=models.IntegerField(default=data.models.current_timestamp),
        ),
    ]
