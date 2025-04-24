from django.http import JsonResponse
from .models import Week
import json
from django.core.cache import cache
from datetime import datetime, timedelta
from finnomenaGold.models import Gold_TH

CACHE_TIMEOUT = 3600
def get_select_predict_week(request):
    if request.method == 'GET':
        date_param=request.GET.get('date')
        if not date_param:
            return JsonResponse({'error': 'Missing date parameter'}, status=400)
        try:
            # แปลง string เป็น datetime object
            date_obj = datetime.strptime(date_param, '%d-%m-%Y').date()
        except ValueError:
            return JsonResponse({'error': 'Invalid date format, should be DD-MM-YYYY'}, status=400)
        display = request.GET.get('display')
        use_cache = request.GET.get('cache', 'true').lower() == 'true'
        cache_key = f"get_select_predict:{display}{date_obj}"
        if use_cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                return JsonResponse(cached_data, safe=False)
        # ค้นหา record ที่มี date ตรงกับที่ส่งมา
        week_data_predict = Week.objects.filter(date=date_obj).values()
        week_data_actual = []
        for i in range(1,8,1):
            target_date = week_data_predict[0][f'date_{i}']
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
            date_obj = target_date.strftime('%d-%m-%y')
            gold_buff=Gold_TH.objects.filter(date=date_obj).order_by('-id').values().first()
            if gold_buff:
                week_data_actual.append(gold_buff)
        if display == 'chart':
            result=[]
            if not week_data_actual:
                result=[{"status": "success",
                     "predict_data": list(week_data_predict),
                    "actual_data": ''}]
                cache.set(cache_key,result , timeout=CACHE_TIMEOUT)
                return JsonResponse(list(result), safe=False)
            for i in range(7):
                buff_result=[{"label":"Created At",
                            "data":week_data_actual[i]['created_at']},
                            {"label":"Timestamp",
                            "data":week_data_actual[i]['timestamp']},
                            {"label":"Date",
                            "data":week_data_actual[i]['date']},
                            {"label":"Price",
                            "data":week_data_actual[i]['price']}
                            ]
                result.append(buff_result)
            result=[{"status": "success",
                     "predict_data": list(week_data_predict),
                    "actual_data": list(result)}]
            cache.set(cache_key,result , timeout=CACHE_TIMEOUT)
            return JsonResponse(list(result), safe=False)
        if not week_data_predict:
            return JsonResponse({'error': 'No Predict data found for the given date'}, status=404)
        elif not week_data_actual:
            return JsonResponse({'error': 'No Actual data found for the given date'}, status=404)
        result=[{"status": "success",
            "predict_data": list(week_data_predict),
            "actual_data": list(week_data_actual)}]
        cache.set(cache_key,result , timeout=CACHE_TIMEOUT)
        return JsonResponse(list(result), safe=False)
    
    return JsonResponse({'error': 'GET method required'}, status=405)

def get_predict_date(request):
    if request.method == 'GET':
        use_cache = request.GET.get('cache', 'true').lower() == 'true'
        cache_key = f"get_predict_date"
        if use_cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                return JsonResponse(cached_data, safe=False)
        # ค้นหา record ที่มี date ตรงกับที่ส่งมา
        week_data_predict = Week.objects.all().values('date')

        if not week_data_predict:
            return JsonResponse({'error': 'No Predict data found for the given date'}, status=404)
        cache.set(cache_key,list(week_data_predict) , timeout=CACHE_TIMEOUT)
        return JsonResponse(list(week_data_predict), safe=False)
    
    return JsonResponse({'error': 'GET method required'}, status=405)