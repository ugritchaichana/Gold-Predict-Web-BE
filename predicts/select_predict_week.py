from django.http import JsonResponse
from .models import Week
import json
from django.core.cache import cache
from datetime import datetime, timedelta
from finnomenaGold.models import Gold_TH
import logging
import requests
import pandas as pd
from collections import OrderedDict
from datetime import datetime

logger = logging.getLogger(__name__)
CACHE_TIMEOUT = 3600
def get_select_predict_week(request):
    if request.method == 'GET':
        display = request.GET.get('display')
        date_param=request.GET.get('date')
        use_cache = request.GET.get('cache', 'true').lower() == 'true'
        cache_key = f"get_select_predict:{display}{date_param}"
        print(f'Cache:{cache_key}')
        if use_cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                return JsonResponse(cached_data, safe=False)
        if not date_param:
            return JsonResponse({'error': 'Missing date parameter'}, status=400)
        try:
            # แปลง string เป็น datetime object
            date_obj = datetime.strptime(date_param, '%d-%m-%Y').date()
        except ValueError:
            return JsonResponse({'error': 'Invalid date format, should be DD-MM-YYYY'}, status=400)

        # ค้นหา record ที่มี date ตรงกับที่ส่งมา
        week_data_predict = Week.objects.filter(date_1=date_obj).values()
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
            for i in week_data_actual:
                result.append([{"label":"Created At",
                            "data":i['created_at']},
                            {"label":"Timestamp",
                            "data":i['timestamp']},
                            {"label":"Date",
                            "data":i['date']},
                            {"label":"Price",
                            "data":i['price']}
                            ])
            result=[{"status": "success",
                     "predict_data": list(week_data_predict),
                    "actual_data": list(result)}]
            cache.set(cache_key,result , timeout=CACHE_TIMEOUT)
            logger.info(f"Generated cache key: {cache_key}")
            return JsonResponse(list(result), safe=False)

        if not week_data_predict:
            return JsonResponse({'error': 'No Predict data found for the given date'}, status=404)
        
        if not week_data_actual:
                result=[{"status": "success",
                     "predict_data": list(week_data_predict),
                    "actual_data": ''}]
                cache.set(cache_key,result , timeout=CACHE_TIMEOUT)
                return JsonResponse(list(result), safe=False)
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
        week_data_predict = Week.objects.all().values('date_1')

        if not week_data_predict:
            return JsonResponse({'error': 'No Predict data found for the given date'}, status=404)
        cache.set(cache_key,list(week_data_predict) , timeout=CACHE_TIMEOUT)
        return JsonResponse(list(week_data_predict), safe=False)
    
    return JsonResponse({'error': 'GET method required'}, status=405)

def set_cache_select_predict(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'GET method required'}, status=405)

    display = request.GET.get('display')

    # 1. โหลด predict dataframe
    Predict_df = list(Week.objects.order_by('-id').values())

    # 2. หาเก่าสุด และใหม่สุด
    # oldest_date = min(item['date'] for item in Predict_df)
    # newest_date = max(item['date'] for item in Predict_df)

    # 3. เอา oldest_date ไปแปลง format เฉยๆ (จริงๆอาจไม่จำเป็นด้วยซ้ำ)
    # date_obj = datetime.strptime(oldest_date, "%Y-%m-%d")
    # oldest_date = date_obj.strftime("%d-%m-%Y")
    # date_obj = datetime.strptime(newest_date, "%Y-%m-%d")
    # newest_date = date_obj.strftime("%d-%m-%Y")

    # 4. โหลดข้อมูล actual ตามช่วงวันที่
    Actual_df = Gold_TH.objects.all().order_by('-id')
    # 5. latest_per_day: หาข้อมูลที่ timestamp ใหม่สุดของแต่ละวัน
    
    latest_per_day = OrderedDict()
    # for rec in Actual_df:
    #     # print(vars(rec))
    for rec in Actual_df:
        if rec.date not in latest_per_day:
            latest_per_day[rec.date] = {
            'date': rec.date,
            'price': rec.price,
            'timestamp': rec.timestamp,
            'created_at': rec.created_at,
        }    
               
    # print(latest_per_day.get('28-04-25'))
    for predict in Predict_df:
        week_data_actual = []

        # เอาวันที่ของ predict มาแปลงเป็น string dd-mm-yy
        buff_date = predict['date_1']
        buff_date = datetime.strptime(buff_date, '%Y-%m-%d').date()
        buff_date = buff_date.strftime('%d-%m-%Y')

        # เตรียม cache key
        cache_key = f"get_select_predict:{display}{buff_date}"

        # loop หา actual ของ date_1 ถึง date_7
        for i in range(1, 8):
            target_date = predict.get(f'date_{i}')

            if target_date:
                target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
                date_obj = target_date.strftime('%d-%m-%y')
                # print(date_obj)
                # เอาข้อมูลล่าสุดของวันนั้นจาก latest_per_day
                gold_buff = latest_per_day.get(date_obj)

                if gold_buff:
                    week_data_actual.append(gold_buff)

        # เริ่มทำ result ที่จะ cache
        result = []

        if not week_data_actual:
            # ถ้าไม่มี actual data
            predict = [predict]
            result = [{
                "status": "success",
                "predict_data": predict,   # <-- ต้องใช้ dict() ไม่ใช่ list()
                "actual_data": ''
            }]
        else:
            # ถ้ามี actual data
            actual_result = []
            for i in week_data_actual:
                actual_result.append([
                    {"label": "Created At", "data": i['created_at']},
                    {"label": "Timestamp", "data": i['timestamp']},
                    {"label": "Date", "data": i['date']},
                    {"label": "Price", "data": i['price']}
                ])
            predict = [predict]
            result = [{
                "status": "success",
                "predict_data": list(predict),  # <-- แก้ list เป็น dict
                "actual_data": actual_result
            }]

        # เซ็ตเข้า cache
        print(f'cache={cache_key}')
        cache.set(cache_key, result, timeout=CACHE_TIMEOUT)
        # return JsonResponse(list(result), safe=False)
        logger.info(f"Generated cache key: {cache_key}")