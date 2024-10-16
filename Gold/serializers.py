from rest_framework import serializers
from .models import Gold_THB, Gold_USD, Gold_CNY

class GoldTHBSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gold_THB
        fields = '__all__'

class GoldUSDSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gold_USD
        fields = '__all__'

class GoldCNYSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gold_CNY
        fields = '__all__'
