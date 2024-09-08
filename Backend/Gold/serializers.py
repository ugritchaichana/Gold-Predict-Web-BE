from rest_framework import serializers
from .models import GoldPrice

class DailyGoldPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoldPrice
        fields = ['date', 'gold_price']
