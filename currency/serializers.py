from rest_framework import serializers
from .models import USDTHB, CNYTHB

class USDTHBSerializer(serializers.ModelSerializer):
    class Meta:
        model = USDTHB
        fields = '__all__'

class CNYTHBSerializer(serializers.ModelSerializer):
    class Meta:
        model = CNYTHB
        fields = '__all__'
