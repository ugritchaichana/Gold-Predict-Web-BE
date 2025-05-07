from django.http import JsonResponse
from .models import Week
from django.core.cache import cache
import json
from datetime import datetime 
from django.utils import timezone
from finnomenaGold.models import Gold_TH
CACHE_TIMEOUT = 3600

def get_week(request):
    if request.method == 'GET':
        display = request.GET.get('display')
        use_cache = request.GET.get('cache', 'true').lower() == 'true'
        get_model = request.GET.get('model','1').lower()
        if get_model not in [str(i) for i in range(1, 8 + 1)]:
            return JsonResponse({'error': 'model must be a number between 1 and 8'}, status=400)
        cache_key = f"get_week:{display}{get_model}"
        if use_cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                return JsonResponse(cached_data, safe=False)
        last_date = Gold_TH.objects.order_by('-id').values('date').first()
        print(last_date['date'])
        last_date =datetime.strptime(last_date['date'],'%d-%m-%y')
        weeks = list(Week.objects.all().values('date_1', 'date_2', 'date_3', 'date_4', 'date_5', 'date_6', 'date_7','price_1', 'price_2', 'price_3', 'price_4', 'price_5', 'price_6', 'price_7','created_at'))
        if display == 'chart':
            labels = []
            data = []
            created_at=[]
            today_str = last_date.strftime("%Y-%m-%d")
            for i,w in enumerate(weeks):
                # if i == len(weeks) - 1:
                #     for d in range(1, 8):
                #         labels.append(w[f'date_{d}'])
                #         data.append(w[f'price_{d}'])
                # else:
                if today_str==w[f'date_{get_model}']:
                    labels.append(w[f'date_{get_model}'])
                    data.append(w[f'price_{get_model}'])
                    created_at.append(timezone.localtime(w['created_at']))
                    if i<len(weeks)-1:
                        # print(f'i={i} week={len(weeks)}')
                        # print(weeks[-1][f'date_{get_model}'])
                        labels.append(weeks[-1][f'date_{get_model}'])
                        data.append(weeks[-1][f'price_{get_model}'])
                        created_at.append(timezone.localtime(weeks[-1]['created_at']))
                        break
                    else:
                        break
                labels.append(w[f'date_{get_model}'])
                data.append(w[f'price_{get_model}'])
                # print(w)
                created_at.append(timezone.localtime(w['created_at']))
            chart_result = {'labels': labels, 'data': data,'created_at':created_at}
            cache.set(cache_key, chart_result, timeout=CACHE_TIMEOUT)
            return JsonResponse(chart_result, safe=False)
        if display == 'chart2':
         try:
            labels = []
            data = []
            today_str = last_date.strftime("%Y-%m-%d")
            for i,w in enumerate(weeks):
                # if i == len(weeks) - 1:
                #     for d in range(1, 8):
                #         labels.append(w[f'date_{d}'])
                #         data.append(w[f'price_{d}'])
                # else:
                if today_str==w[f'date_{get_model}']:
                    labels.append(w[f'date_{get_model}'])
                    data.append(w[f'price_{get_model}'])
                    if i<len(weeks)-1:
                        # print(f'i={i} week={len(weeks)}')
                        # print(weeks[-1][f'date_{get_model}'])
                        labels.append(weeks[-1][f'date_{get_model}'])
                        data.append(weeks[-1][f'price_{get_model}'])
                        break
                    else:
                        break
                labels.append(w[f'date_{get_model}'])
                data.append(w[f'price_{get_model}'])
                # print(w)
            timestamps = [
                datetime.strptime(date_str, "%Y-%m-%d").timestamp()
                for date_str in labels
                ]
            chart_result = [
                {'Predict': p, 'time': int(t)}
                for t, p in zip(timestamps, data)
            ]
            cache.set(cache_key, chart_result, timeout=CACHE_TIMEOUT)
            return JsonResponse(chart_result, safe=False)
         except Exception as e:
             return JsonResponse({"error":str(e)})
        result = []
        for i, w in enumerate(weeks):
            if i == len(weeks) - 1:
            #     result.append({
            #         'date_1': w['date_1'],
            #         'date_2': w['date_2'],
            #         'date_3': w['date_3'],
            #         'date_4': w['date_4'],
            #         'date_5': w['date_5'],
            #         'date_6': w['date_6'],
            #         'date_7': w['date_7'],
            #         'price_1': w['price_1'],
            #         'price_2': w['price_2'],
            #         'price_3': w['price_3'],
            #         'price_4': w['price_4'],
            #         'price_5': w['price_5'],
            #         'price_6': w['price_6'],
            #         'price_7': w['price_7'],
            #     })
            # else:
                result.append({
                    'date': w[f'date_{get_model}'],
                    'price': w[f'price_{get_model}']
                })
        if use_cache:
            cache.set(cache_key, result, timeout=CACHE_TIMEOUT)
        return JsonResponse(result, safe=False)
    return JsonResponse({'error': 'GET method required'}, status=405)