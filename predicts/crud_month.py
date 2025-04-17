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
            month_predict=data.get('month_predict')
        )
        return JsonResponse({'status': 'success', 'month': month.id})

def delete_all_month(request):
    if request.method == 'GET':
        try:
            deleted_count, _ = Month.objects.all().delete()
            return JsonResponse({
                'status': 'success', 
                'message': f'All month data deleted successfully. {deleted_count} records removed.'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error', 
                'message': f'Failed to delete all month data: {str(e)}'
            }, status=500)
    return JsonResponse({
        'status': 'error', 
        'message': 'Only DELETE method is allowed'
    }, status=405)

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
                'month_predict': month.month_predict
            }
        })
    except Month.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Month not found'}, status=404)

def read_all_months(request):
    if request.method == 'GET':
        months = Month.objects.all()
        month_list = [
            {
                'timestamp': month.timestamp,
                'open': month.open,
                'high': month.high,
                'low': month.low,
                'date': month.date,
                'created_at': month.created_at,
                'month_predict': month.month_predict
            }
            for month in months
        ]
        return JsonResponse({'status': 'success', 'months': month_list})

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
            month.month_predict = data.get('month_predict', month.month_predict)
            month.save()
            print(f"Updated month_predict: {month.month_predict}")  # Debug statement
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
