from django.core.cache import cache
from django.http import JsonResponse
from finnomenaGold.views import get_gold_data
from currency.views import get_currency_data
from predicts.select_predict_week import get_predict_date,get_select_predict_week
import requests
from django.http import HttpRequest, QueryDict
from datetime import datetime
import json
gold_query_choice=[0,1]
gold_query_frame=['7d',
                  '1m',
                  '1y',
                  'all']
def set_cache(request):
    if request.method=='GET':
        try:
            to_request = HttpRequest    
            to_request.method='GET'
            for index_choice in range(len(gold_query_choice)):
                for index_frame in range(len(gold_query_frame)):        
                    to_request.GET=QueryDict(f'db_choice={gold_query_choice[index_choice]}&max=100&frame={gold_query_frame[index_frame]}&cache=True')
                    get_gold_data(to_request)
            for index_frame in range(len(gold_query_frame)):
                to_request.GET=QueryDict(f'frame={gold_query_frame[index_frame]}&cache=True&max=100&display=chart')
                get_currency_data(to_request)
            to_request = HttpRequest    
            to_request.method='GET'
            res = get_predict_date(to_request)
            dates_list = [item['date'] for item in json.loads(res.content)]
            new_dates_list = [
                datetime.strptime(date_str, "%Y-%m-%d").strftime("%d-%m-%Y")
                for date_str in dates_list
            ]
            for index_date in range(len(new_dates_list)):
                 to_request.GET=QueryDict(f'date={new_dates_list[index_date]}&display=chart')
                 get_select_predict_week(to_request)
            return JsonResponse({'statue':'success'})
        except:
            return JsonResponse({'error':'cannot set cache'})