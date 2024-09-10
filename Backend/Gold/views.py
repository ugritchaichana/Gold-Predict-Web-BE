from django.shortcuts import render
from django.http import HttpResponse,JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import GoldPrice
from .serializers import DailyGoldPriceSerializer
import requests
from bs4 import BeautifulSoup
from django.utils import timezone


def index(request):
    return HttpResponse("get : http://127.0.0.1:8000/api/scrapegoldth/")

def scrape_gold_price(request):
    url = 'https://www.goldtraders.or.th/'
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        span_element = soup.find('span', id='DetailPlace_uc_goldprices1_lblBLSell')

        if span_element:
            try:
                price = float(span_element.get_text(strip=True).replace(',', ''))

                data = {
                    'date': timezone.now().date(),
                    'gold_price': price
                }
                
                serializer = DailyGoldPriceSerializer(data=data)
                if serializer.is_valid():
                    gold_price_obj = serializer.save()
                    return JsonResponse({
                        'id': gold_price_obj.id,
                        'date': gold_price_obj.date,
                        'gold_price': gold_price_obj.gold_price
                    }, status=201)
                else:
                    return JsonResponse(serializer.errors, status=400)
            except ValueError:
                return JsonResponse({'error': 'Invalid price format'}, status=400)

        return JsonResponse({'error': 'Price element not found'}, status=404)

    return JsonResponse({'error': 'Failed to retrieve data'}, status=response.status_code)