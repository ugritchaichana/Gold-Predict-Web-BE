from django.http import JsonResponse
from .models import Week
from django.core.cache import cache
import json
from datetime import datetime, timedelta

CACHE_TIMEOUT = 3600

def get_week(request):
    if request.method == 'GET':
        display = request.GET.get('display')
        use_cache = request.GET.get('cache', 'true').lower() == 'true'
        cache_key = f"get_week:{display}"
        if use_cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                return JsonResponse(cached_data, safe=False)
        weeks = list(Week.objects.all().values('date_1', 'date_2', 'date_3', 'date_4', 'date_5', 'date_6', 'date_7','price_1', 'price_2', 'price_3', 'price_4', 'price_5', 'price_6', 'price_7'))
        if display == 'chart':
            labels = []
            data = []
            for i, w in enumerate(weeks):
                if i == len(weeks) - 1:
                    for d in range(1, 8):
                        labels.append(w[f'date_{d}'])
                        data.append(w[f'price_{d}'])
                else:
                    labels.append(w['date_1'])
                    data.append(w['price_1'])
            chart_result = {'labels': labels, 'data': data}
            if use_cache:
                cache.set(cache_key, chart_result, timeout=CACHE_TIMEOUT)
            return JsonResponse(chart_result, safe=False)
        result = []
        for i, w in enumerate(weeks):
            if i == len(weeks) - 1:
                result.append({
                    'date_1': w['date_1'],
                    'date_2': w['date_2'],
                    'date_3': w['date_3'],
                    'date_4': w['date_4'],
                    'date_5': w['date_5'],
                    'date_6': w['date_6'],
                    'date_7': w['date_7'],
                    'price_1': w['price_1'],
                    'price_2': w['price_2'],
                    'price_3': w['price_3'],
                    'price_4': w['price_4'],
                    'price_5': w['price_5'],
                    'price_6': w['price_6'],
                    'price_7': w['price_7'],
                })
            else:
                result.append({
                    'date_1': w['date_1'],
                    'price_1': w['price_1']
                })
        if use_cache:
            cache.set(cache_key, result, timeout=CACHE_TIMEOUT)
        return JsonResponse(result, safe=False)
    return JsonResponse({'error': 'GET method required'}, status=405)