from rest_framework import serializers
from .models import GoldPriceTH

class GoldPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoldPriceTH
        fields = '__all__'
