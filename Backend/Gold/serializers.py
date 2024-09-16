from rest_framework import serializers
from .models import DailyGoldPrice

class DailyGoldPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyGoldPrice
        fields = ['date', 'gold_price']
