# Gold_US\serializers.py

from rest_framework import serializers
from .models import GoldPriceUS

class GoldPriceXAUAPISerializer(serializers.ModelSerializer):
    class Meta:
        model = GoldPriceUS
        fields = '__all__'

class CSVUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
