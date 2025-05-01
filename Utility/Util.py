from django.core.cache import cache
from django.http import JsonResponse
from finnomenaGold.views import get_gold_data
from currency.views import get_currency_data
from predicts.select_predict_week import set_cache_select_predict,get_predict_date
from predicts.get_week import get_week
import requests
from django.http import HttpRequest, QueryDict
from datetime import datetime
import json
def set_cache(request):
    if request.method=='GET':
        try:
            to_request = HttpRequest    
            to_request.method='GET'
            for i in range(0,1):
                to_request.GET=QueryDict(f'db_choice={i}&frame=all&display=chart&max=100')
                get_gold_data(to_request)
                to_request.GET=QueryDict(f'db_choice={i}&frame=7d&display=chart')
                get_gold_data(to_request)
                to_request.GET=QueryDict(f'db_choice={i}&frame=1m&display=chart')
                get_gold_data(to_request)
                to_request.GET=QueryDict(f'db_choice={i}&frame=1y&display=chart&max=100')
                get_gold_data(to_request)
            to_request.GET=QueryDict(f'frame=1y&cache=True&display=chart&max=50')
            get_currency_data(to_request)
            to_request.GET=QueryDict(f'frame=1m&cache=True&display=chart')
            get_currency_data(to_request)
            to_request.GET=QueryDict(f'frame=all&cache=True&display=chart&max=50')
            get_currency_data(to_request)
            to_request.GET=QueryDict(f'frame=7d&cache=True&display=chart')
            get_currency_data(to_request)
            to_request = HttpRequest    
            to_request.method='GET'
            for i in range(1,8):
                to_request.GET=QueryDict(f'cache=false&display=chart&model={i}')
                get_week(to_request)
            to_request = HttpRequest    
            to_request.method='GET'
            to_request.GET=QueryDict(f'cache=false')
            get_predict_date(to_request)
            to_request = HttpRequest    
            to_request.method='GET'
            to_request.GET=QueryDict(f'display=chart')
            set_cache_select_predict(to_request)
            return JsonResponse({'statue':'success'})
        except:
            return JsonResponse({'error':'cannot set cache'})