from django.shortcuts import render
from django.http import HttpResponse,JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import GoldPrice
from .serializers import DailyGoldPriceSerializer

def index(request):
    return HttpResponse("Booth-Test")

def gold(request):
    data = {
        'key1': 'value1',
        'key2': 'value2',
        'key3': [1, 2, 3]
    }
    return JsonResponse(data)

class DailyGoldPriceView(APIView):
    def post(self, request):
        # print(getGoldData())
        # print(request.data)
        # print('✅date>', request.data.get('date'))
        serializer = DailyGoldPriceSerializer(data=request.data)
        if serializer.is_valid():
            # serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

def getGoldData() :
    return 'test'