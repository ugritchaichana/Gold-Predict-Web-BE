from django.http import JsonResponse
from .models import Week
import json

def create_week(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        week = Week.objects.create(
            timestamp=data.get('timestamp'),
            price_0=data.get('price_0'),
            price_1=data.get('price_1'),
            price_2=data.get('price_2'),
            price_3=data.get('price_3'),
            price_4=data.get('price_4'),
            price_5=data.get('price_5'),
            price_6=data.get('price_6'),
            price_7=data.get('price_7'),
            date=data.get('date'),
            created_at=data.get('created_at'),
        )
        return JsonResponse({'status': 'success', 'id': week.id})

def read_week(request, week_id=None):
    range_param = request.GET.get('range', 'latest')

    if week_id:
        week = Week.objects.filter(id=week_id).first()
        if week:
            return JsonResponse({
                'status': 'success',
                'week': {
                    'timestamp': week.timestamp,
                    'price_0': week.price_0,
                    'price_1': week.price_1,
                    'price_2': week.price_2,
                    'price_3': week.price_3,
                    'price_4': week.price_4,
                    'price_5': week.price_5,
                    'price_6': week.price_6,
                    'price_7': week.price_7,
                    'date': week.date,
                    'created_at': week.created_at,
                }
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Week not found'
            })
    
    elif range_param == 'all':
        weeks = Week.objects.all()
        week_list = [{
            'timestamp': week.timestamp,
            'price_0': week.price_0,
            'price_1': week.price_1,
            'price_2': week.price_2,
            'price_3': week.price_3,
            'price_4': week.price_4,
            'price_5': week.price_5,
            'price_6': week.price_6,
            'price_7': week.price_7,
            'date': week.date,
            'created_at': week.created_at
        } for week in weeks]

        return JsonResponse({
            'status': 'success',
            'weeks': week_list
        })
    
    else:
        latest_week = Week.objects.latest('created_at')  # หรือใช้ timestamp หากต้องการ
        week_data = {
            'timestamp': latest_week.timestamp,
            'price_0': latest_week.price_0,
            'price_1': latest_week.price_1,
            'price_2': latest_week.price_2,
            'price_3': latest_week.price_3,
            'price_4': latest_week.price_4,
            'price_5': latest_week.price_5,
            'price_6': latest_week.price_6,
            'price_7': latest_week.price_7,
            'date': latest_week.date,
            'created_at': latest_week.created_at
        }
        return JsonResponse({
            'status': 'success',
            'week': week_data
        })

def update_week(request):
    week_id = request.GET.get('id')
    if not week_id:
        return JsonResponse({
            'status': 'error',
            'message': 'week_id is required for update'
        }, status=400)

    if request.method == 'PUT':
        data = json.loads(request.body)
        try:
            week = Week.objects.get(id=week_id)
            week.timestamp = data.get('timestamp', week.timestamp)
            week.price_0 = data.get('price_0', week.price_0)
            week.price_1 = data.get('price_1', week.price_1)
            week.price_2 = data.get('price_2', week.price_2)
            week.price_3 = data.get('price_3', week.price_3)
            week.price_4 = data.get('price_4', week.price_4)
            week.price_5 = data.get('price_5', week.price_5)
            week.price_6 = data.get('price_6', week.price_6)
            week.price_7 = data.get('price_7', week.price_7)
            week.date = data.get('date', week.date)
            week.created_at = data.get('created_at', week.created_at)
            week.save()
            return JsonResponse({'status': 'success', 'week-id': week.id})
        except Week.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Week not found'}, status=404)

def delete_week(request):
    week_id = request.GET.get('week_id')
    if not week_id:
        return JsonResponse({
            'status': 'error',
            'message': 'week_id is required for delete'
        }, status=400)

    if request.method == 'DELETE':
        try:
            week = Week.objects.get(id=week_id)
            week.delete()
            return JsonResponse({'status': 'success', 'message': 'Week deleted'})
        except Week.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Week not found'}, status=404)