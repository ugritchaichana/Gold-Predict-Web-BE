# Gold_US\serializers.py

from rest_framework import serializers
from .models import GoldPriceXAU_API

class GoldPriceXAUAPISerializer(serializers.ModelSerializer):
    class Meta:
        model = GoldPriceXAU_API
        fields = '__all__'

class CSVUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
