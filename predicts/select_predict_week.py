from django.http import JsonResponse
from .models import Week
import json
from datetime import datetime, timedelta
from finnomenaGold.models import Gold_TH

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
        

        if not week_data_predict:
            return JsonResponse({'error': 'No Predict data found for the given date'}, status=404)
        elif not week_data_actual:
            return JsonResponse({'error': 'No Actual data found for the given date'}, status=404)
        return JsonResponse({
            'predict_data': list(week_data_predict),
            'actual_data': list(week_data_actual)
        }, safe=False)
    
    return JsonResponse({'error': 'GET method required'}, status=405)

def get_predict_date(request):
    if request.method == 'GET':

        # ค้นหา record ที่มี date ตรงกับที่ส่งมา
        week_data_predict = Week.objects.all().values('date')

        if not week_data_predict:
            return JsonResponse({'error': 'No Predict data found for the given date'}, status=404)
        return JsonResponse(list(week_data_predict), safe=False)
    
    return JsonResponse({'error': 'GET method required'}, status=405)