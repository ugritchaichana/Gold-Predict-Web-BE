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

        return JsonResponse({"message": f"Data fetched and saved successfully. {len(bulk_data)} new records added."})
    else:
        return JsonResponse({"error": "Failed to fetch data from Finnomena Gold TH API.", "status_code": response.status_code}, status=500)

def fetch_gold_us_data(request):
    # initial data 
    url = f"https://www.finnomena.com/fn3/api/polygon/gold/spot/v2/aggs/ticker/C%3AXAUUSD/range/1/day/2005-01-01/{currentDateTime}"
    # initial data
    daysAgo5 = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
    # url = f"https://www.finnomena.com/fn3/api/polygon/gold/spot/v2/aggs/ticker/C%3AXAUUSD/range/1/day/{daysAgo5}/{currentDateTime}"
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

        return JsonResponse({"message": f"Data fetched and saved successfully. {len(bulk_data)} new records added."})
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
                start_timeframe = (end_timeframe - timedelta(days=30)).replace(day=1)
            elif frame == "3m":
                start_timeframe = (end_timeframe - timedelta(days=90)).replace(day=1)
            elif frame == "6m":
                start_timeframe = (end_timeframe - timedelta(days=180)).replace(day=1)
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

        else:
            logging.debug("Invalid 'group_by' parameter.")
            return JsonResponse({"error": "Invalid 'group_by' parameter. Use 'daily' or 'monthly'."}, status=400)

        logging.debug(f"Data count: {len(data)}")
        logging.debug(f"Data: {data}")

        return JsonResponse({
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
        
        return JsonResponse({
            "status": "success",
            "data": data
        })
        
    except LookupError:
        return JsonResponse({"status": "error", "message": f"Model '{table_name}' does not exist in app 'finnomenaGold'."}, status=400)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)