from django.http import JsonResponse
from .models import Month
import json

def create_month(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        month = Month.objects.create(
            timestamp=data.get('timestamp'),
            open=data.get('open'),
            high=data.get('high'),
            low=data.get('low'),
            date=data.get('date'),
            created_at=data.get('created_at'),
        )
        return JsonResponse({'status': 'success', 'month': month.id})

def read_month(request, month_id):
    try:
        month = Month.objects.get(id=month_id)
        return JsonResponse({
            'status': 'success',
            'month': {
                'timestamp': month.timestamp,
                'open': month.open,
                'high': month.high,
                'low': month.low,
                'date': month.date,
                'created_at': month.created_at,
            }
        })
    except Month.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Month not found'}, status=404)

def update_month(request, month_id):
    if request.method == 'PUT':
        data = json.loads(request.body)
        try:
            month = Month.objects.get(id=month_id)
            month.timestamp = data.get('timestamp', month.timestamp)
            month.open = data.get('open', month.open)
            month.high = data.get('high', month.high)
            month.low = data.get('low', month.low)
            month.date = data.get('date', month.date)
            month.created_at = data.get('created_at', month.created_at)
            month.save()
            return JsonResponse({'status': 'success', 'month': month.id})
        except Month.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Month not found'}, status=404)

def delete_month(request, month_id):
    if request.method == 'DELETE':
        try:
            month = Month.objects.get(id=month_id)
            month.delete()
            return JsonResponse({'status': 'success', 'message': 'Month deleted'})
        except Month.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Month not found'}, status=404)
