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
            date_1=data.get('date_1'),
            date_2=data.get('date_2'),
            date_3=data.get('date_3'),
            date_4=data.get('date_4'),
            date_5=data.get('date_5'),
            date_6=data.get('date_6'),
            date_7=data.get('date_7'),
            date=data.get('date'),
            created_at=data.get('created_at'),
        )
        return JsonResponse({'status': 'success', 'id': week.id})

def delete_all_week(request):
    if request.method == 'GET':
        try:
            deleted_count, _ = Week.objects.all().delete()
            return JsonResponse({
                'status': 'success', 
                'message': f'All week data deleted successfully. {deleted_count} records removed.'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error', 
                'message': f'Failed to delete all week data: {str(e)}'
            }, status=500)
    return JsonResponse({
        'status': 'error', 
        'message': 'Only DELETE method is allowed'
    }, status=405)

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
        if (max_val and len(data) > int(max_val)):
            max_val = int(max_val)
            
            # If max_val is less than 2, return at least first point
            if max_val < 2:
                return [data[0]]
                
            # Always include first and last points
            selected = [data[0]]
            
            # If we have more than 2 points to select, distribute the middle ones evenly
            if max_val > 2:
                # Calculate step size for the middle points (excluding first and last)
                step = (len(data) - 1) / (max_val - 1)
                
                # Add the middle points (excluding first which was already added and last which will be added)
                for i in range(1, max_val - 1):
                    idx = int(i * step)
                    selected.append(data[idx])
            
            # Add the last point
            selected.append(data[-1])
            
            return selected
        return data

    def format_chart_data(data, date_key, price_key):
        labels = []
        formatted_data = []
        for item in data:
            if item.get(price_key) is not None:
                # แปลงรูปแบบวันที่จาก yyyy-MM-dd เป็น dd-MM-yyyy
                original_date = item[date_key]
                date_obj = datetime.strptime(original_date, '%Y-%m-%d')
                formatted_date = date_obj.strftime('%d-%m-%Y')
                labels.append(formatted_date)
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

    elif range_param == 'sort_all_old':
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

    elif range_param == 'sort_all':
        start_date = request.GET.get('startdate', "2000-01-01")
        end_date = request.GET.get('enddate', (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'))
        # Add a parameter to control whether to include rawData in the response
        include_raw_data = request.GET.get('rawData', 'true').lower() != 'false'
        
        weeks = Week.objects.filter(date__range=[start_date, end_date])
        result = []
        for week in weeks:
            predictions = {
                'id': week.id,
                'Prediction date': week.date,
                'Prediction prices': {}
            }

            base_date = datetime.strptime(week.date, '%Y-%m-%d')
            for i in range(8):
                date = (base_date + timedelta(days=i)).strftime('%Y-%m-%d')
                price = getattr(week, f'price_{i}')
                if price is not None:
                    predictions['Prediction prices'][date] = round(price, 2)
            result.append(predictions)

        filtered_result = []
        
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
        
        latest_prediction_date = None
        latest_prediction_datetime = None
        if result:
            for week in result:
                prediction_date = week['Prediction date']
                prediction_datetime = datetime.strptime(prediction_date, '%Y-%m-%d')
                if latest_prediction_datetime is None or prediction_datetime > latest_prediction_datetime:
                    latest_prediction_datetime = prediction_datetime
                    latest_prediction_date = prediction_date
        
        date_predictions = {}
        
        for week in result:
            prediction_date = week['Prediction date']
            for date, price in week['Prediction prices'].items():
                date_datetime = datetime.strptime(date, '%Y-%m-%d')
                
                if date_datetime < start_datetime or date_datetime > end_datetime:
                    continue
                
                if date not in date_predictions or prediction_date > date_predictions[date]['Prediction date']:
                    date_predictions[date] = {
                        'Prediction date': prediction_date,
                        'date': date,
                        'price': price
                    }
        
        current_date = start_datetime
        while current_date <= end_datetime:
            current_date_str = current_date.strftime('%Y-%m-%d')
            if current_date_str not in date_predictions:
                for week in sorted(result, key=lambda x: x['Prediction date'], reverse=True):
                    if current_date_str in week['Prediction prices']:
                        date_predictions[current_date_str] = {
                            'Prediction date': week['Prediction date'],
                            'date': current_date_str,
                            'price': week['Prediction prices'][current_date_str]
                        }
                        break
            current_date += timedelta(days=1)
        
        filtered_result = sorted(date_predictions.values(), key=lambda x: x['date'])
        
        if latest_prediction_date:
            latest_week = next((w for w in result if w['Prediction date'] == latest_prediction_date), None)
            if latest_week:
                for date, price in latest_week['Prediction prices'].items():
                    date_datetime = datetime.strptime(date, '%Y-%m-%d')
                    if date_datetime > end_datetime:
                        filtered_result.append({
                            'Prediction date': latest_prediction_date,
                            'date': date,
                            'price': price
                        })
        
        filtered_result = apply_max(filtered_result, max_points)
        
        if display == 'chart':
            return JsonResponse(format_chart_data(filtered_result, 'date', 'price'))
        
        # Prepare the response with conditional rawData inclusion
        response_data = {
            'startDate': start_date,
            'endDate': end_date,
            'filtered_data': filtered_result
        }
        
        # Only include rawData if parameter is true
        if include_raw_data:
            response_data['rawData'] = result
            
        return JsonResponse(response_data)

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