# Generated by Django 5.1.1 on 2024-10-15 19:46

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CNYTHB',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('price', models.FloatField()),
                ('open', models.FloatField()),
                ('high', models.FloatField()),
                ('low', models.FloatField()),
                ('percent', models.FloatField()),
                ('diff', models.FloatField()),
            ],
            options={
                'db_table': 'cnythb',
            },
        ),
        migrations.CreateModel(
            name='USDTHB',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('price', models.FloatField()),
                ('open', models.FloatField()),
                ('high', models.FloatField()),
                ('low', models.FloatField()),
                ('percent', models.FloatField()),
                ('diff', models.FloatField()),
            ],
            options={
                'db_table': 'usdthb',
            },
        ),
    ]
