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

# def read_week(request, week_id=None):
#     range_param = request.GET.get('range', 'latest')

#     if week_id:
#         week = Week.objects.filter(id=week_id).first()
#         if week:
#             return JsonResponse({
#                 'status': 'success',
#                 'week': {
#                     'timestamp': week.timestamp,
#                     'price_0': week.price_0,
#                     'price_1': week.price_1,
#                     'price_2': week.price_2,
#                     'price_3': week.price_3,
#                     'price_4': week.price_4,
#                     'price_5': week.price_5,
#                     'price_6': week.price_6,
#                     'price_7': week.price_7,
#                     'date': week.date,
#                     'created_at': week.created_at,
#                 }
#             })
#         else:
#             return JsonResponse({
#                 'status': 'error',
#                 'message': 'Week not found'
#             })
    
#     elif range_param == 'all':
#         weeks = Week.objects.all()
#         week_list = [{
#             'timestamp': week.timestamp,
#             'price_0': week.price_0,
#             'price_1': week.price_1,
#             'price_2': week.price_2,
#             'price_3': week.price_3,
#             'price_4': week.price_4,
#             'price_5': week.price_5,
#             'price_6': week.price_6,
#             'price_7': week.price_7,
#             'date': week.date,
#             'created_at': week.created_at
#         } for week in weeks]

#         return JsonResponse({
#             'status': 'success',
#             'weeks': week_list
#         })
    
#     else:
#         latest_week = Week.objects.latest('created_at')  # หรือใช้ timestamp หากต้องการ
#         week_data = {
#             'timestamp': latest_week.timestamp,
#             'price_0': latest_week.price_0,
#             'price_1': latest_week.price_1,
#             'price_2': latest_week.price_2,
#             'price_3': latest_week.price_3,
#             'price_4': latest_week.price_4,
#             'price_5': latest_week.price_5,
#             'price_6': latest_week.price_6,
#             'price_7': latest_week.price_7,
#             'date': latest_week.date,
#             'created_at': latest_week.created_at
#         }
#         return JsonResponse({
#             'status': 'success',
#             'week': week_data
#         })


def read_week(request, week_id=None):
    range_param = request.GET.get('range', 'latest')
    date_param = request.GET.get('date')
    
    from datetime import datetime, timedelta

    if week_id:
        week = Week.objects.filter(id=week_id).first()
        if week:
            # Calculate 8 dates starting from the week's date
            base_date = datetime.strptime(week.date, '%Y-%m-%d')
            dates = [(base_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(8)]
            
            return JsonResponse({
                'status': 'success',
                'week': {
                    'timestamp': week.timestamp,
                    dates[0]: week.price_0,
                    dates[1]: week.price_1,
                    dates[2]: week.price_2,
                    dates[3]: week.price_3,
                    dates[4]: week.price_4,
                    dates[5]: week.price_5,
                    dates[6]: week.price_6,
                    dates[7]: week.price_7,
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
        week_list = []
        
        for week in weeks:
            base_date = datetime.strptime(week.date, '%Y-%m-%d')
            dates = [(base_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(8)]
            
            week_data = {
                'date': week.date,
                'created_at': week.created_at,
                'timestamp': week.timestamp,
                dates[0]: week.price_0,
                dates[1]: week.price_1,
                dates[2]: week.price_2,
                dates[3]: week.price_3,
                dates[4]: week.price_4,
                dates[5]: week.price_5,
                dates[6]: week.price_6,
                dates[7]: week.price_7
            }
            week_list.append(week_data)

        return JsonResponse({
            'status': 'success',
            'weeks': week_list
        })
    
    elif date_param:
        try:
            # Try to find a Week record with the specified date
            week = Week.objects.filter(date=date_param).first()
            
            # If no record found for the date, get the closest date
            if not week:
                # Try to get the closest date available (first checking future dates, then past dates)
                future_week = Week.objects.filter(date__gt=date_param).order_by('date').first()
                past_week = Week.objects.filter(date__lt=date_param).order_by('-date').first()
                
                if future_week and past_week:
                    # Calculate which date is closer
                    future_date = datetime.strptime(future_week.date, '%Y-%m-%d')
                    past_date = datetime.strptime(past_week.date, '%Y-%m-%d')
                    requested_date = datetime.strptime(date_param, '%Y-%m-%d')
                    
                    if (future_date - requested_date) < (requested_date - past_date):
                        week = future_week
                    else:
                        week = past_week
                elif future_week:
                    week = future_week
                elif past_week:
                    week = past_week
                else:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'No week data available'
                    })
            
            # Format the response
            base_date = datetime.strptime(week.date, '%Y-%m-%d')
            dates = [(base_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(8)]
            
            week_data = {
                'date': week.date,
                'created_at': week.created_at,
                'timestamp': week.timestamp,
                dates[0]: week.price_0,
                dates[1]: week.price_1,
                dates[2]: week.price_2,
                dates[3]: week.price_3,
                dates[4]: week.price_4,
                dates[5]: week.price_5,
                dates[6]: week.price_6,
                dates[7]: week.price_7
            }
            
            return JsonResponse({
                'status': 'success',
                'week': week_data
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error processing date: {str(e)}'
            })
    
    else:
        try:
            # Get today's date in the format YYYY-MM-DD
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Try to find a Week record with today's date
            week = Week.objects.filter(date=today).first()
            
            # If no record found for today, get the latest record
            if not week:
                week = Week.objects.latest('created_at')
                
            base_date = datetime.strptime(week.date, '%Y-%m-%d')
            dates = [(base_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(8)]
            
            week_data = {
                'date': week.date,
                'created_at': week.created_at,
                'timestamp': week.timestamp,
                dates[0]: week.price_0,
                dates[1]: week.price_1,
                dates[2]: week.price_2,
                dates[3]: week.price_3,
                dates[4]: week.price_4,
                dates[5]: week.price_5,
                dates[6]: week.price_6,
                dates[7]: week.price_7
            }
            
            return JsonResponse({
                'status': 'success',
                'week': week_data
            })
        except Week.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'No week data available'
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