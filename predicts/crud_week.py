from django.http import JsonResponse
from .models import Week
import json
from datetime import datetime, timedelta

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

def read_week(request, week_id=None):
    range_param = request.GET.get('range', 'latest')
    date_param = request.GET.get('date')
    display = request.GET.get('display')
    max_points = request.GET.get('max')
    startdate = request.GET.get('startdate')
    enddate = request.GET.get('enddate')

    # Validate date parameters
    start_date = None
    end_date = None
    if startdate or enddate:
        try:
            if not startdate or not enddate:
                raise ValueError("Both startdate and enddate are required")
            start_date = datetime.strptime(startdate, '%Y-%m-%d')
            end_date = datetime.strptime(enddate, '%Y-%m-%d')
            if start_date > end_date:
                raise ValueError("startdate must be before enddate")
        except ValueError as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    def apply_max(data, max_val):
        if max_val and len(data) > int(max_val):
            max_val = int(max_val)
            step = len(data) / max_val
            current = 0.0
            selected = []
            for _ in range(max_val):
                idx = int(current)
                selected.append(data[idx])
                current += step
            return selected
        return data

    def format_chart_data(data, date_key, price_key):
        labels = []
        formatted_data = []
        for item in data:
            if item.get(price_key) is not None:
                labels.append(item[date_key])
                formatted_data.append(round(item[price_key], 2))
        return {'labels': labels, 'data': formatted_data}

    def filter_by_date_range(data, date_key):
        if start_date and end_date:
            filtered = []
            for item in data:
                item_date = datetime.strptime(item[date_key], '%Y-%m-%d')
                if start_date <= item_date <= end_date:
                    filtered.append(item)
            return filtered
        return data

    if week_id:
        week = Week.objects.filter(id=week_id).first()
        if week:
            base_date = datetime.strptime(week.date, '%Y-%m-%d')
            dates = [(base_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(8)]
            week_data = {
                'status': 'success',
                'week': {
                    'id': week.id,
                    'date': week.date,
                    'created_at': week.created_at.isoformat() if week.created_at else None,
                    'timestamp': datetime.fromtimestamp(week.timestamp).isoformat() if week.timestamp else None,
                    **{date: getattr(week, f'price_{i}') for i, date in enumerate(dates)}
                }
            }
            if display == 'chart':
                chart_data = []
                for i in range(8):
                    date = dates[i]
                    price = getattr(week, f'price_{i}')
                    if price is not None:
                        chart_data.append({
                            'date': date,
                            'price': round(price, 2)
                        })
                chart_data = apply_max(chart_data, max_points)
                return JsonResponse(format_chart_data(chart_data, 'date', 'price'))
            return JsonResponse(week_data)
        else:
            return JsonResponse({'status': 'error', 'message': 'Week not found'}, status=404)

    elif range_param == 'all':
        weeks = Week.objects.all().order_by('id')
        week_list = []
        flattened_data = []
        for week in weeks:
            base_date = datetime.strptime(week.date, '%Y-%m-%d')
            dates = [(base_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(8)]
            week_data = {
                'id': week.id,
                'date': week.date,
                'created_at': week.created_at.isoformat() if week.created_at else None,
                'timestamp': datetime.fromtimestamp(week.timestamp).isoformat() if week.timestamp else None,
                **{date: getattr(week, f'price_{i}') for i, date in enumerate(dates)}
            }
            week_list.append(week_data)
            for i in range(8):
                date_str = dates[i]
                price = getattr(week, f'price_{i}')
                if price is not None:
                    flattened_data.append({
                        'date': date_str,
                        'price': round(price, 2)
                    })
        
        flattened_data = filter_by_date_range(flattened_data, 'date')
        flattened_data = apply_max(flattened_data, max_points)
        if display == 'chart':
            return JsonResponse(format_chart_data(flattened_data, 'date', 'price'))
        return JsonResponse({'status': 'success', 'weeks': week_list}, safe=False)

    elif range_param == 'sort_all':
        weeks = Week.objects.all().order_by('id')
        week_list = []
        for week in weeks:
            base_date = datetime.strptime(week.date, '%Y-%m-%d')
            dates = [(base_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(8)]
            week_data = {
                'id': week.id,
                'date': week.date,
                'created_at': week.created_at.isoformat() if week.created_at else None,
                'timestamp': datetime.fromtimestamp(week.timestamp).isoformat() if week.timestamp else None,
                **{date: getattr(week, f'price_{i}') for i, date in enumerate(dates)}
            }
            week_list.append(week_data)

        filtered_data = []
        for week in week_list:
            base_date = datetime.strptime(week['date'], '%Y-%m-%d')
            date_predict = (base_date + timedelta(days=1)).strftime('%Y-%m-%d')
            price = week.get(date_predict)
            if price is not None:
                filtered_data.append({
                    'date': date_predict,
                    'price': round(price, 2)
                })
        
        filtered_data = filter_by_date_range(filtered_data, 'date')
        filtered_data = apply_max(filtered_data, max_points)
        if display == 'chart':
            return JsonResponse(format_chart_data(filtered_data, 'date', 'price'))
        else:
            return JsonResponse({
                'status': 'success',
                'start': week_list[0]['date'] if week_list else None,
                'end': week_list[-1]['date'] if week_list else None,
                'filtered_data': filtered_data,
                'weeks': week_list
            }, safe=False)

    elif date_param:
        try:
            week = Week.objects.filter(date=date_param).first()
            if not week:
                future_week = Week.objects.filter(date__gt=date_param).order_by('date').first()
                past_week = Week.objects.filter(date__lt=date_param).order_by('-date').first()
                if future_week and past_week:
                    future_date = datetime.strptime(future_week.date, '%Y-%m-%d')
                    past_date = datetime.strptime(past_week.date, '%Y-%m-%d')
                    requested_date = datetime.strptime(date_param, '%Y-%m-%d')
                    week = future_week if (future_date - requested_date) < (requested_date - past_date) else past_week
                else:
                    week = future_week or past_week
            if not week:
                return JsonResponse({'status': 'error', 'message': 'No week data available'}, status=404)

            base_date = datetime.strptime(week.date, '%Y-%m-%d')
            dates = [(base_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(8)]
            week_data = {
                'status': 'success',
                'week': {
                    'id': week.id,
                    'date': week.date,
                    'created_at': week.created_at.isoformat() if week.created_at else None,
                    'timestamp': datetime.fromtimestamp(week.timestamp).isoformat() if week.timestamp else None,
                    **{date: getattr(week, f'price_{i}') for i, date in enumerate(dates)}
                }
            }
            if display == 'chart':
                chart_data = []
                for i in range(8):
                    date = dates[i]
                    price = getattr(week, f'price_{i}')
                    if price is not None:
                        chart_data.append({
                            'date': date,
                            'price': round(price, 2)
                        })
                chart_data = apply_max(chart_data, max_points)
                chart_data = filter_by_date_range(chart_data, 'date')
                return JsonResponse(format_chart_data(chart_data, 'date', 'price'))
            return JsonResponse(week_data)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Error processing date: {str(e)}'}, status=400)

    else:
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            week = Week.objects.filter(date=today).first()
            if not week:
                week = Week.objects.latest('created_at')
            base_date = datetime.strptime(week.date, '%Y-%m-%d')
            dates = [(base_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(8)]
            week_data = {
                'status': 'success',
                'week': {
                    'id': week.id,
                    'date': week.date,
                    'created_at': week.created_at.isoformat() if week.created_at else None,
                    'timestamp': datetime.fromtimestamp(week.timestamp).isoformat() if week.timestamp else None,
                    **{date: getattr(week, f'price_{i}') for i, date in enumerate(dates)}
                }
            }
            if display == 'chart':
                chart_data = []
                for i in range(8):
                    date = dates[i]
                    price = getattr(week, f'price_{i}')
                    if price is not None:
                        chart_data.append({
                            'date': date,
                            'price': round(price, 2)
                        })
                chart_data = apply_max(chart_data, max_points)
                chart_data = filter_by_date_range(chart_data, 'date')
                return JsonResponse(format_chart_data(chart_data, 'date', 'price'))
            return JsonResponse(week_data)
        except Week.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'No week data available'}, status=404)