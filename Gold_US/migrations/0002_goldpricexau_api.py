# Generated by Django 5.1.1 on 2024-09-29 19:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Gold_US', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='GoldPriceXAU_API',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField()),
                ('timestamp', models.BigIntegerField()),
                ('metal', models.CharField(max_length=10)),
                ('exchange', models.CharField(max_length=20)),
                ('currency', models.CharField(max_length=10)),
                ('price', models.FloatField()),
                ('prev_close_price', models.FloatField()),
                ('ch', models.FloatField()),
                ('chp', models.FloatField()),
                ('price_gram_24k', models.FloatField()),
                ('price_gram_22k', models.FloatField()),
                ('price_gram_21k', models.FloatField()),
                ('price_gram_20k', models.FloatField()),
                ('price_gram_18k', models.FloatField()),
                ('price_gram_16k', models.FloatField()),
                ('price_gram_14k', models.FloatField()),
                ('price_gram_10k', models.FloatField()),
            ],
        ),
    ]