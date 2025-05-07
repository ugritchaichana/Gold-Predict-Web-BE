import time
import requests
from django.http import JsonResponse
from django.apps import apps
from datetime import datetime, timezone, timedelta
from django.db.models import Avg, Min, Max
from django.db import transaction
from django.core.cache import cache
import logging
import decimal
from collections import OrderedDict

# Set cache timeout (in seconds)
CACHE_TIMEOUT = 3600  # 1 hour

logging.basicConfig(level=logging.DEBUG)
currentDateTime = datetime.now().strftime('%Y-%m-%d')

def fetch_gold_data(request):
    db_choice = request.GET.get('db_choice')
    if not db_choice:
        return JsonResponse({"error": "Missing 'db_choice' parameter."}, status=400)

    table_mapping = {
        '0': 'Gold_TH',
        '1': 'Gold_US',
        '2': 'currency'
    }

    table_name = table_mapping.get(db_choice)
    if not table_name:
        return JsonResponse({"error": "Invalid 'db_choice' parameter value."}, status=400)

    if db_choice == '0':
        return fetch_gold_th_data(request)
    elif db_choice == '1':
        return fetch_gold_us_data(request)
    else:
        return JsonResponse({"error": "Invalid 'db_choice' parameter value."}, status=400)

def fetch_gold_th_data(request):
    # url = "https://www.finnomena.com/fn3/api/gold/trader/history/graph?period=MAX&sampling=0&startTimeframe="
    url = "https://www.finnomena.com/fn3/api/gold/trader/history/graph?period=5D&sampling=0&startTimeframe="

    contry_table = apps.get_model('finnomenaGold', 'Gold_TH')

    response = requests.get(url)
    if response.status_code == 200:
        try:
            data = response.json().get("data", [])
            if not isinstance(data, list):
                raise ValueError("Expected 'data' to be a list.")
        except (ValueError, TypeError) as e:
            return JsonResponse({"error": f"Error parsing response data: {str(e)}"}, status=500)

        bulk_data = []
        existing_timestamps = set(contry_table.objects.values_list("timestamp", flat=True))

        for item in data:
            if item["timestamp"] not in existing_timestamps:
                created_at = datetime.strptime(item["createdAt"], '%Y-%m-%dT%H:%M:%SZ')

                bulk_data.append(
                    contry_table(
                        timestamp=item["timestamp"],
                        created_at=created_at,
                        created_time=item["createdTime"],
                        price=item["barBuyPrice"],
                        bar_sell_price=item["barSellPrice"],
                        bar_price_change=item["barPriceChange"],
                        ornament_buy_price=item["ornamentBuyPrice"],
                        ornament_sell_price=item["ornamentSellPrice"],
                        date=created_at.strftime('%d-%m-%y'),
                    )
                )

        if bulk_data:
            with transaction.atomic():
                contry_table.objects.bulk_create(bulk_data, batch_size=5000)
        
        # Clear memory
        data = None
        bulk_data = None
        existing_timestamps = None
        import gc
        gc.collect()  # Force garbage collection

        return JsonResponse({"message": f"Data fetched and saved successfully. {len(bulk_data) if bulk_data else 0} new records added."})
    else:
        return JsonResponse({"error": "Failed to fetch data from Finnomena Gold TH API.", "status_code": response.status_code}, status=500)

def fetch_gold_us_data(request):
    # initial data 
    # url = f"https://www.finnomena.com/fn3/api/polygon/gold/spot/v2/aggs/ticker/C%3AXAUUSD/range/1/day/2025-01-01/{currentDateTime}"
    # url = f"https://www.finnomena.com/fn3/api/polygon/gold/spot/v2/aggs/ticker/C%3AXAUUSD/range/1/day/2005-01-01/{currentDateTime}"
    # initial data

    url = f"https://www.finnomena.com/fn3/api/polygon/gold/spot/v2/aggs/ticker/C%3AXAUUSD/range/1/day/{(datetime.now()-timedelta(days=5)).strftime('%Y-%m-%d')}/{currentDateTime}"
    contry_table = apps.get_model('finnomenaGold', 'Gold_US')
    print(f"✅ > url us : {url}")

    response = requests.get(url)
    if response.status_code == 200:
        try:
            data = response.json().get("data", {})
            results = data.get("results", [])
            if not isinstance(results, list):
                raise ValueError("Expected 'results' to be a list.")
        except (ValueError, TypeError) as e:
            return JsonResponse({"error": f"Error parsing response data: {str(e)}"}, status=500)

        bulk_data = []
        existing_timestamps = set(contry_table.objects.values_list("timestamp", flat=True))

        for item in results:
            timestamp = item.get("t")
            if timestamp and timestamp not in existing_timestamps:
                timestamp_local = time.localtime(timestamp / 1000)
                timestamp_gmt7 = time.mktime(timestamp_local) + 7 * 3600
                created_at = datetime.fromtimestamp(timestamp_gmt7)

                bulk_data.append(
                    contry_table(
                        timestamp=timestamp,
                        price=item.get("o"),
                        close_price=item.get("c"),
                        high_price=item.get("h"),
                        low_price=item.get("l"),
                        volume=item.get("v"),
                        volume_weight_avg=item.get("vw"),
                        num_transactions=item.get("n"),
                        date=created_at.strftime('%d-%m-%y'),
                        created_at=created_at,
                    )
                )

        if bulk_data:
            with transaction.atomic():
                contry_table.objects.bulk_create(bulk_data, batch_size=5000)

        # Clear memory
        data = None
        results = None
        bulk_data = None
        existing_timestamps = None
        import gc
        gc.collect()  # Force garbage collection
        
        return JsonResponse({"message": f"Data fetched and saved successfully. {len(bulk_data) if bulk_data else 0} new records added."})
    else:
        return JsonResponse({"error": "Failed to fetch data from Finnomena Gold US API.", "status_code": response.status_code}, status=500)

def delete_all_gold_data(request):
    contry_table_name = request.GET.get('contry_table')
    if not contry_table_name:
        return JsonResponse({"error": "Missing 'contry_table' parameter."}, status=400)

    try:
        contry_table = apps.get_model('finnomenaGold', contry_table_name)
        contry_table.objects.all().delete()
        return JsonResponse({"message": "All records deleted successfully."})
    except LookupError:
        return JsonResponse({"error": f"Model '{contry_table_name}' does not exist in app 'finnomenaGold'."}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def create_gold_data(request):
    """
    Creates new gold data entries from POST request data.
    Expects JSON body with:
    - db_choice: '0' for Gold_TH, '1' for Gold_US
    - data: list of objects with model fields
    """
    if request.method != 'POST':
        return JsonResponse({"error": "Only POST method is allowed."}, status=405)
    
    try:
        import json
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body."}, status=400)
    
    db_choice = data.get('db_choice')
    if not db_choice:
        return JsonResponse({"error": "Missing 'db_choice' parameter."}, status=400)
    
    table_mapping = {'0': 'Gold_TH', '1': 'Gold_US'}
    table_name = table_mapping.get(db_choice)
    
    if not table_name:
        return JsonResponse({"error": "Invalid 'db_choice' parameter value. Must be 0 or 1."}, status=400)
    
    records = data.get('data', [])
    if not records or not isinstance(records, list):
        return JsonResponse({"error": "Missing or invalid 'data' parameter. Must be a list of records."}, status=400)
    
    try:
        contry_table = apps.get_model('finnomenaGold', table_name)
        bulk_data = []
        
        for record in records:
            if db_choice == '0':  # Gold_TH
                # Convert string datetime to datetime object if provided
                created_at = record.get('created_at')
                if isinstance(created_at, str):
                    try:
                        created_at = datetime.strptime(created_at, '%Y-%m-%dT%H:%M:%SZ')
                    except ValueError:
                        return JsonResponse({"error": f"Invalid datetime format in record. Use 'YYYY-MM-DDTHH:MM:SSZ'."}, status=400)
                elif not created_at:
                    created_at = datetime.now()
                
                # Set timestamp if not provided
                timestamp = record.get('timestamp')
                if not timestamp:
                    timestamp = int(created_at.timestamp() * 1000)
                
                # Set date if not provided
                date = record.get('date')
                if not date:
                    date = created_at.strftime('%d-%m-%y')
                
                bulk_data.append(
                    contry_table(
                        timestamp=timestamp,
                        created_at=created_at,
                        created_time=record.get('created_time'),
                        price=record.get('price'),
                        bar_sell_price=record.get('bar_sell_price'),
                        bar_price_change=record.get('bar_price_change'),
                        ornament_buy_price=record.get('ornament_buy_price'),
                        ornament_sell_price=record.get('ornament_sell_price'),
                        date=date
                    )
                )
                
            elif db_choice == '1':  # Gold_US
                # Convert string datetime to datetime object if provided
                created_at = record.get('created_at')
                if isinstance(created_at, str):
                    try:
                        created_at = datetime.strptime(created_at, '%Y-%m-%dT%H:%M:%SZ')
                    except ValueError:
                        return JsonResponse({"error": f"Invalid datetime format in record. Use 'YYYY-MM-DDTHH:MM:SSZ'."}, status=400)
                elif not created_at:
                    created_at = datetime.now()
                
                # Set timestamp if not provided
                timestamp = record.get('timestamp')
                if not timestamp:
                    timestamp = int(created_at.timestamp() * 1000)
                
                # Set date if not provided
                date = record.get('date')
                if not date:
                    date = created_at.strftime('%d-%m-%y')
                
                bulk_data.append(
                    contry_table(
                        timestamp=timestamp,
                        price=record.get('price'),
                        close_price=record.get('close_price'),
                        high_price=record.get('high_price'),
                        low_price=record.get('low_price'),
                        volume=record.get('volume'),
                        volume_weight_avg=record.get('volume_weight_avg'),
                        num_transactions=record.get('num_transactions'),
                        date=date,
                        created_at=created_at
                    )
                )
        
        if bulk_data:
            with transaction.atomic():
                created_records = contry_table.objects.bulk_create(bulk_data, batch_size=5000)
            
            # Fetch the created data for verification
            created_data = []
            for record in created_records:
                record_dict = {}
                for field in record._meta.fields:
                    field_name = field.name
                    field_value = getattr(record, field_name)
                    
                    # Convert datetime objects to string format
                    if isinstance(field_value, datetime):
                        field_value = field_value.strftime('%Y-%m-%dT%H:%M:%SZ')
                    # Convert Decimal objects to float for JSON serialization
                    elif isinstance(field_value, decimal.Decimal):
                        field_value = float(field_value)
                        
                    record_dict[field_name] = field_value
                
                created_data.append(record_dict)
            
            return JsonResponse({
                "status": "success",
                "message": f"Data created successfully. {len(bulk_data)} new records added.",
                "created_records": created_data
            })
        else:
            return JsonResponse({
                "status": "warning",
                "message": "No data was created."
            })
            
    except LookupError:
        return JsonResponse({"error": f"Model '{table_name}' does not exist in app 'finnomenaGold'."}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def get_gold_by_id(request, id=None):
    """
    Retrieves gold data by specific ID.
    URL parameters:
    - db_choice: '0' for Gold_TH, '1' for Gold_US
    - id: The ID of the record to retrieve (can also be passed in the URL path)
    """
    db_choice = request.GET.get('db_choice')
    
    # Allow ID to be passed either in URL path or as a query parameter
    record_id = id or request.GET.get('id')
    
    if not db_choice:
        return JsonResponse({"status": "error", "message": "Missing 'db_choice' parameter."}, status=400)
    
    if not record_id:
        return JsonResponse({"status": "error", "message": "Missing 'id' parameter."}, status=400)
    
    table_mapping = {'0': 'Gold_TH', '1': 'Gold_US'}
    table_name = table_mapping.get(db_choice)
    
    if not table_name:
        return JsonResponse({"status": "error", "message": "Invalid 'db_choice' parameter value. Must be 0 or 1."}, status=400)
    
    try:
        # Ensure record_id is a valid integer
        try:
            record_id = int(record_id)
        except ValueError:
            return JsonResponse({"status": "error", "message": f"Invalid ID format: '{record_id}'. ID must be an integer."}, status=400)
        
        cache_key = f"gold_data:{db_choice}:{record_id}"
        cached_data = cache.get(cache_key)
        if cached_data:
            logging.debug(f"Cache hit for key: {cache_key}")
            return JsonResponse({"status": "success", "data": cached_data})
        
        contry_table = apps.get_model('finnomenaGold', table_name)
        record = contry_table.objects.filter(id=record_id).first()
        
        if not record:
            return JsonResponse({
                "status": "error",
                "message": f"No record found with ID {record_id} in {table_name}."
            }, status=404)
        
        # Convert model instance to dictionary
        data = {}
        for field in record._meta.fields:
            field_name = field.name
            field_value = getattr(record, field_name)
            
            # Convert datetime objects to string format
            if isinstance(field_value, datetime):
                field_value = field_value.strftime('%Y-%m-%dT%H:%M:%SZ')
            # Convert Decimal objects to float for JSON serialization
            elif isinstance(field_value, decimal.Decimal):
                field_value = float(field_value)
                
            data[field_name] = field_value
            
        cache.set(cache_key, data, timeout=CACHE_TIMEOUT)  # Cache using standard timeout
        logging.debug(f"Cache set for key: {cache_key}")
        
        return JsonResponse({
            "status": "success",
            "data": data
        })
        
    except LookupError:
        return JsonResponse({"status": "error", "message": f"Model '{table_name}' does not exist in app 'finnomenaGold'."}, status=400)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


def apply_max(data, max_val):
    """
    Apply max parameter to limit the number of data points while ensuring first and last points are included.
    Data points between first and last are distributed evenly.
    """
    if max_val and len(data) > int(max_val):
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

def convert_dates_to_str(obj):
    import datetime
    if isinstance(obj, dict):
        return {k: convert_dates_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_dates_to_str(i) for i in obj]
    elif isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    else:
        return obj

def get_gold_data(request):
    logging.debug("Entering get_gold_data function")
    db_choice = request.GET.get('db_choice', None)
    if (db_choice is None):
        logging.debug("Missing 'db_choice' parameter.")
        return JsonResponse({"error": "Missing 'db_choice' parameter."}, status=400)

    table_mapping = {'0': 'Gold_TH', '1': 'Gold_US'}
    table_name = table_mapping.get(db_choice)
    if not table_name:
        logging.debug("Invalid 'db_choice' parameter value.")
        return JsonResponse({"error": "Invalid 'db_choice' parameter value. Must be 0 or 1."}, status=400)

    end_timeframe = datetime.now(timezone.utc).date()
    start_timeframe = None

    frame = request.GET.get('frame', None)
    start_param = request.GET.get('start', None)
    end_param = request.GET.get('end', None)
    group_by = request.GET.get('group_by', 'daily')
    use_cache = request.GET.get('cache', 'true').lower() == 'true'
    max_points = request.GET.get('max')
    display = request.GET.get('display', None)  # New parameter for chart display

    try:
        if start_param:
            start_timeframe = datetime.strptime(start_param, "%d-%m-%Y").date()
        if end_param:
            end_timeframe = datetime.strptime(end_param, "%d-%m-%Y").date()

        if start_timeframe and end_timeframe and start_timeframe > end_timeframe:
            logging.debug("'start' date cannot be after 'end' date.")
            return JsonResponse({"error": "'start' date cannot be after 'end' date."}, status=400)

        show_latest_only = False

        if not start_timeframe and frame:
            logging.debug(f"Frame parameter provided: {frame}")
            if frame == "1d":
                show_latest_only = True
                start_timeframe = end_timeframe
            elif frame == "7d":
                start_timeframe = end_timeframe - timedelta(days=6)
            elif frame == "15d":
                start_timeframe = end_timeframe - timedelta(days=14)
            elif frame == "1m":
                # Fix: Show last 30 days instead of just current month
                start_timeframe = end_timeframe - timedelta(days=30)
            elif frame == "3m":
                start_timeframe = end_timeframe - timedelta(days=90)
            elif frame == "6m":
                start_timeframe = end_timeframe - timedelta(days=180)
            elif frame == "1y":
                start_timeframe = end_timeframe.replace(year=end_timeframe.year - 1)
            elif frame == "3y":
                start_timeframe = end_timeframe.replace(year=end_timeframe.year - 3)
            elif frame == "all":
                start_timeframe = None
            else:
                logging.debug("Invalid 'frame' parameter.")
                return JsonResponse({"status": "error", "message": "Invalid 'frame' parameter."}, status=400)

        table_model = apps.get_model('finnomenaGold', table_name)

        cache_key = f"gold_data:{db_choice}:{frame}:{start_timeframe}:{end_timeframe}:{group_by}:{max_points}:{display}"
        if use_cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                logging.debug(f"Cache hit for key: {cache_key}")
                
                if display == 'chart':
                    return JsonResponse({
                        "status": "success",
                        "data": cached_data,
                        "start_date": start_timeframe.strftime('%Y-%m-%d %H:%M:%S.000 %z') if start_timeframe else None,
                        "end_date": end_timeframe.strftime('%Y-%m-%d %H:%M:%S.000 %z') if end_timeframe else None,
                        "default_dates_used": {
                            "start": start_param,
                            "end": datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f %z')
                        }
                    })
                elif display == 'chart2':
                    return JsonResponse(list(cached_data),safe=False)
                return JsonResponse({
                    "cache": [{"status": "used cache", "database": "redis"}],
                    "count": len(cached_data),
                    "data": cached_data
                })

        queryset = table_model.objects.all()

        if frame == "1d" and show_latest_only:
            logging.debug("Frame is 1d and show_latest_only is True")
            latest_record = queryset.order_by('-created_at').first()
            if latest_record:
                start_timeframe = latest_record.created_at.date()
                end_timeframe = latest_record.created_at.date()
                queryset = queryset.filter(created_at__date=start_timeframe)
            else:
                logging.debug("No data available")
                queryset = queryset.none()

            if not queryset.exists():
                logging.debug("No data found for 1d, fetching data for 7d")
                start_timeframe = end_timeframe - timedelta(days=6)
                queryset = table_model.objects.filter(created_at__date__gte=start_timeframe, created_at__date__lte=end_timeframe).order_by('-created_at')
                if queryset.exists():
                    latest_record = queryset.first()
                    queryset = queryset.filter(id=latest_record.id)
                else:
                    logging.debug("No data available for 7d either")
                    queryset = queryset.none()
        else:
            if start_timeframe:
                queryset = queryset.filter(created_at__date__gte=start_timeframe)
            if end_timeframe and queryset.filter(created_at__date__lte=end_timeframe).exists():
                queryset = queryset.filter(created_at__date__lte=end_timeframe)
            elif end_timeframe:
                closest_date = table_model.objects.filter(created_at__date__lt=end_timeframe).order_by('-created_at').first()
                if closest_date:
                    end_timeframe = closest_date.created_at.date()
                    queryset = queryset.filter(created_at__date__lte=end_timeframe)

        logging.debug(f"Start timeframe: {start_timeframe}, End timeframe: {end_timeframe}")
        logging.debug(f"Queryset count before grouping: {queryset.count()}")

        if group_by == "daily":
            queryset = queryset.order_by('created_at')
            data = list(queryset.values())
            data_sorted = sorted(data, key=lambda x: x['created_at'], reverse=True)

            unique_by_day = OrderedDict()
            for row in data_sorted:
                day = row['created_at'].date()
                if day not in unique_by_day:
                    unique_by_day[day] = row

            # 🔽 เรียงวันจากน้อยไปมาก
            data = sorted(unique_by_day.values(), key=lambda x: x['created_at'].date())
            
            # Apply max parameter to limit data points if provided
            if max_points:
                data = apply_max(data, max_points)

        elif group_by == "monthly":
            queryset = queryset.values("created_at__year", "created_at__month").annotate(
                avg_price=Avg("price"),
                min_price=Min("price"),
                max_price=Max("price")
            ).order_by("created_at__year", "created_at__month")

            data = [
                {
                    "period": f"{entry['created_at__year']}-{entry['created_at__month']:02d}",
                    "avg_price": entry["avg_price"],
                    "min_price": entry["min_price"],
                    "max_price": entry["max_price"]
                }
                for entry in queryset
            ]
            
            # Apply max parameter to limit data points if provided
            if max_points:
                data = apply_max(data, max_points)

        else:
            logging.debug("Invalid 'group_by' parameter.")
            return JsonResponse({"error": "Invalid 'group_by' parameter. Use 'daily' or 'monthly'."}, status=400)

        logging.debug(f"Data count: {len(data)}")
        logging.debug(f"Data: {data}")


        # Format data as chart if requested
        if display == 'chart':
            if db_choice == '0':  # Gold_TH
                chart_data = format_chart_data_th(data)
                if use_cache:
                    chart_data_serialized = convert_dates_to_str(chart_data)
                    cache.set(cache_key, chart_data_serialized, timeout=CACHE_TIMEOUT)
                    logging.debug(f"Cache set for key: {cache_key}")
            elif db_choice == '1':  # Gold_US
                chart_data = format_chart_data_us(data)
                if use_cache:
                    chart_data_serialized = convert_dates_to_str(chart_data)
                    cache.set(cache_key, chart_data_serialized, timeout=CACHE_TIMEOUT)
                    logging.debug(f"Cache set for key: {cache_key}")
            return JsonResponse({
                "status": "success",
                "data": chart_data,
                "start_date": start_timeframe.strftime('%Y-%m-%d %H:%M:%S.000 %z') if start_timeframe else None,
                "end_date": end_timeframe.strftime('%Y-%m-%d %H:%M:%S.000 %z') if end_timeframe else None,
                "default_dates_used": {
                    "start": start_param,
                    "end": datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f %z')
                }
            })
        elif display == 'chart2':
            if db_choice == '0':  # Gold_TH
             try:
                result =[{
                        "Bar Buy":line['price'],
                        "Bar Sell":line['bar_sell_price'],
                        "Oranment Buy":line['ornament_buy_price'],
                        "Ornament Sell":line['ornament_sell_price'],
                        "Price Change":line['bar_price_change'],
                        "time":line['timestamp']
                        }
                        for line in data
                        ]
                cache.set(cache_key, result, timeout=CACHE_TIMEOUT)
                return JsonResponse(list(result), safe=False)
             except Exception as e:
                 return JsonResponse({"error":str(e)})
            elif db_choice == '1':  # Gold_US
             try: 
                result =[{
                        "open":line['price'],
                        "high":line['high_price'],
                        "low":line['low_price'],
                        "close":line['close_price'],
                        "timestamp":line['timestamp']
                        }
                        for line in data
                        ]
                cache.set(cache_key, result, timeout=CACHE_TIMEOUT)
                return JsonResponse(list(result), safe=False)
             except Exception as e:
                 return JsonResponse({"error":str(e)})
        return JsonResponse({
            "cache": [{"status": "no used cache", "database": "postgresql"}],
            "count": len(data),
            "data": data
        })

    except ValueError:
        logging.debug("Invalid date format.")
        return JsonResponse({"error": "Invalid date format. Use 'dd-mm-yyyy'."}, status=400)
    except LookupError:
        logging.debug(f"Model '{table_name}' does not exist in app 'finnomenaGold'.")
        return JsonResponse({"error": f"Model '{table_name}' does not exist in app 'finnomenaGold'."}, status=400)
    except Exception as e:
        logging.debug(f"Exception occurred: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)

def format_chart_data_th(data):
    """
    Format Gold_TH data for chart display
    """
    labels = []
    created_at_data = []
    timestamp_data = []
    date_data = []
    price_data = []
    bar_sell_price_data = []
    bar_price_change_data = []
    ornament_buy_price_data = []
    ornament_sell_price_data = []
    
    for item in data:
        labels.append(item.get('date', ''))
        
        # Format created_at as a string if it exists
        created_at = item.get('created_at')
        if created_at is not None:
            if isinstance(created_at, str):
                created_at_data.append(created_at)
            else:
                created_at_data.append(str(created_at))
        else:
            created_at_data.append('')
            
        timestamp_data.append(item.get('timestamp', 0) if item.get('timestamp') is not None else 0)
        date_data.append(item.get('date', '') if item.get('date') is not None else '')
        price_data.append(float(item.get('price', 0)) if item.get('price') is not None else 0)
        bar_sell_price_data.append(float(item.get('bar_sell_price', 0)) if item.get('bar_sell_price') is not None else 0)
        bar_price_change_data.append(float(item.get('bar_price_change', 0)) if item.get('bar_price_change') is not None else 0)
        ornament_buy_price_data.append(float(item.get('ornament_buy_price', 0)) if item.get('ornament_buy_price') is not None else 0)
        ornament_sell_price_data.append(float(item.get('ornament_sell_price', 0)) if item.get('ornament_sell_price') is not None else 0)
    
    return {
        "labels": labels,
        "datasets": [
            { "label": "Created At", "data": created_at_data },
            { "label": "Timestamp", "data": timestamp_data },
            { "label": "Date", "data": date_data },
            { "label": "Price", "data": price_data },
            { "label": "Bar Sell Price", "data": bar_sell_price_data },
            { "label": "Bar Price Change", "data": bar_price_change_data },
            { "label": "Ornament Buy Price", "data": ornament_buy_price_data },
            { "label": "Ornament Sell Price", "data": ornament_sell_price_data }
        ]
    }

def format_chart_data_us(data):
    """
    Format Gold_US data for chart display
    """
    labels = []
    created_at_data = []
    timestamp_data = []
    date_data = []
    price_data = []
    close_price_data = []
    high_price_data = []
    low_price_data = []
    volume_data = []
    volume_weight_avg_data = []
    num_transactions_data = []
    
    for item in data:
        labels.append(item.get('date', ''))
        
        # Format created_at as a string if it exists
        created_at = item.get('created_at')
        if created_at is not None:
            if isinstance(created_at, str):
                created_at_data.append(created_at)
            else:
                created_at_data.append(str(created_at))
        else:
            created_at_data.append('')
            
        timestamp_data.append(item.get('timestamp', 0) if item.get('timestamp') is not None else 0)
        date_data.append(item.get('date', '') if item.get('date') is not None else '')
        price_data.append(float(item.get('price', 0)) if item.get('price') is not None else 0)
        close_price_data.append(float(item.get('close_price', 0)) if item.get('close_price') is not None else 0)
        high_price_data.append(float(item.get('high_price', 0)) if item.get('high_price') is not None else 0)
        low_price_data.append(float(item.get('low_price', 0)) if item.get('low_price') is not None else 0)
        volume_data.append(float(item.get('volume', 0)) if item.get('volume') is not None else 0)
        volume_weight_avg_data.append(float(item.get('volume_weight_avg', 0)) if item.get('volume_weight_avg') is not None else 0)
        num_transactions_data.append(int(item.get('num_transactions', 0)) if item.get('num_transactions') is not None else 0)
    
    return {
        "labels": labels,
        "datasets": [
            { "label": "Created At", "data": created_at_data },
            { "data": timestamp_data },
            { "label": "Date", "data": date_data },
            { "label": "Price", "data": price_data },
            { "label": "Close Price", "data": close_price_data },
            { "label": "High Price", "data": high_price_data },
            { "label": "Low Price", "data": low_price_data },
            { "label": "Volume", "data": volume_data },
            { "label": "Volume Weighted Average", "data": volume_weight_avg_data },
            { "label": "Number of Transactions", "data": num_transactions_data }
        ]
    }
## ข้ามวันอาทิตย์

def subtract_7_days_skipping_sundays(end_date,day):
    days_counted = 0
    current = end_date
    result = []

    while days_counted < day:
        if current.weekday() != 6:  # 6 = วันอาทิตย์
            result.append(current)
            days_counted += 1
        current -= timedelta(days=1)

    return min(result)  # คืนวันเริ่มต้น (วันแรกจาก 7 วันไม่รวมอาทิตย์)