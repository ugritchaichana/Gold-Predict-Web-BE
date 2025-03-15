from django.http import JsonResponse
from predicts.models import Week
from datetime import datetime, timedelta

def read(request):
    if request.method == 'GET':
        start_date = request.GET.get('startdate', "2000-01-01")
        end_date = request.GET.get('enddate', (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'))
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

        # Create filtered_data to show most recent prediction for each date
        filtered_result = []
        
        # Convert string dates to datetime for comparison
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Find the latest prediction date in the data
        latest_prediction_date = None
        latest_prediction_datetime = None
        if result:
            for week in result:
                prediction_date = week['Prediction date']
                prediction_datetime = datetime.strptime(prediction_date, '%Y-%m-%d')
                if latest_prediction_datetime is None or prediction_datetime > latest_prediction_datetime:
                    latest_prediction_datetime = prediction_datetime
                    latest_prediction_date = prediction_date
        
        # Dictionary to store the most recent prediction for each date
        date_predictions = {}
        
        # Process all predictions to find most recent for each date
        for week in result:
            prediction_date = week['Prediction date']
            for date, price in week['Prediction prices'].items():
                date_datetime = datetime.strptime(date, '%Y-%m-%d')
                
                # Skip dates outside the requested range
                if date_datetime < start_datetime or date_datetime > end_datetime:
                    continue
                
                # Check if we already have a prediction for this date or if this one is more recent
                if date not in date_predictions or prediction_date > date_predictions[date]['Prediction date']:
                    date_predictions[date] = {
                        'Prediction date': prediction_date,
                        'date': date,
                        'price': price
                    }
        
        # For dates without a prediction, use the most recent available prediction
        # that has future predictions
        current_date = start_datetime
        while current_date <= end_datetime:
            current_date_str = current_date.strftime('%Y-%m-%d')
            if current_date_str not in date_predictions:
                # Find the most recent prediction that includes this date
                for week in sorted(result, key=lambda x: x['Prediction date'], reverse=True):
                    if current_date_str in week['Prediction prices']:
                        date_predictions[current_date_str] = {
                            'Prediction date': week['Prediction date'],
                            'date': current_date_str,
                            'price': week['Prediction prices'][current_date_str]
                        }
                        break
            current_date += timedelta(days=1)
        
        # Convert dictionary to sorted list
        filtered_result = sorted(date_predictions.values(), key=lambda x: x['date'])
        
        # Check if there are future dates with predictions after the end_date
        # from the latest prediction available
        if latest_prediction_date:
            latest_week = next((w for w in result if w['Prediction date'] == latest_prediction_date), None)
            if latest_week:
                for date, price in latest_week['Prediction prices'].items():
                    date_datetime = datetime.strptime(date, '%Y-%m-%d')
                    # Include future dates that are after the end_date
                    if date_datetime > end_datetime:
                        filtered_result.append({
                            'Prediction date': latest_prediction_date,
                            'date': date,
                            'price': price
                        })
        
        return JsonResponse({
            'startDate': start_date,
            'endDate': end_date,
            'rawData': result,
            'filtered_data': filtered_result
        })