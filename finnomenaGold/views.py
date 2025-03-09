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
    # url = f"https://www.finnomena.com/fn3/api/polygon/gold/spot/v2/aggs/ticker/C%3AXAUUSD/range/1/day/2005-01-01/{currentDateTime}"
    # initial data
    daysAgo5 = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
    url = f"https://www.finnomena.com/fn3/api/polygon/gold/spot/v2/aggs/ticker/C%3AXAUUSD/range/1/day/{daysAgo5}/{currentDateTime}"
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
    db_choice = request.GET.get('db_choice', None)
    if db_choice is None:
        return JsonResponse({"error": "Missing 'db_choice' parameter."}, status=400)

    table_mapping = {'0': 'Gold_TH', '1': 'Gold_US'}
    table_name = table_mapping.get(db_choice)
    if not table_name:
        return JsonResponse({"error": "Invalid 'db_choice' parameter value. Must be 0 or 1."}, status=400)

    end_timeframe = datetime.now(timezone.utc).date()
    start_timeframe = None

    frame = request.GET.get('frame', None)
    start_param = request.GET.get('start', None)
    end_param = request.GET.get('end', None)
    group_by = request.GET.get('group_by', 'daily')

    cache_time = 3600  # Cache time in seconds (1 hour)
    cache_param = request.GET.get('cache', 'True').lower()

    if cache_param == 'false':
        use_cache = False
    else:
        use_cache = True

    try:
        if start_param:
            start_timeframe = datetime.strptime(start_param, "%d-%m-%Y").date()
        if end_param:
            end_timeframe = datetime.strptime(end_param, "%d-%m-%Y").date()

        if start_timeframe and end_timeframe and start_timeframe > end_timeframe:
            return JsonResponse({"error": "'start' date cannot be after 'end' date."}, status=400)

        # ตัวแปรเพื่อบอกว่าต้องการเฉพาะข้อมูลล่าสุด
        show_latest_only = False

        if not start_timeframe and frame:
            if frame == "1d":
                # กรณี 1d ให้ค้นหาข้อมูลล่าสุด 
                show_latest_only = True
                # ยังไม่กำหนดช่วงเวลาตอนนี้ เพราะจะต้องดูก่อนว่ามีข้อมูลวันนี้หรือไม่
                start_timeframe = end_timeframe
            elif frame == "7d":
                start_timeframe = end_timeframe - timedelta(days=6)
                show_latest_only = False
            elif frame == "15d":
                start_timeframe = end_timeframe - timedelta(days=14)
                show_latest_only = False
            elif frame == "1m":
                start_timeframe = (end_timeframe - timedelta(days=30)).replace(day=1)
                show_latest_only = False
            elif frame == "3m":
                start_timeframe = (end_timeframe - timedelta(days=90)).replace(day=1)
                show_latest_only = False
            elif frame == "6m":
                start_timeframe = (end_timeframe - timedelta(days=180)).replace(day=1)
                show_latest_only = False
            elif frame == "1y":
                start_timeframe = end_timeframe.replace(year=end_timeframe.year - 1)
                show_latest_only = False
            elif frame == "3y":
                start_timeframe = end_timeframe.replace(year=end_timeframe.year - 3)
                show_latest_only = False
            elif frame == "all":
                start_timeframe = None
                show_latest_only = False
            else:
                return JsonResponse({"status": "error", "message": "Invalid 'frame' parameter."}, status=400)
        else:
            # กรณีไม่ได้กำหนด frame หรือใช้ start/end โดยตรง
            show_latest_only = False

        table_model = apps.get_model('finnomenaGold', table_name)

        cache_key = f"gold_data:{db_choice}:{frame}:{start_timeframe}:{end_timeframe}:{group_by}"
        count_cache_key = f"gold_data_count:{db_choice}:{group_by}"

        # Start with PostgreSQL as default
        cache_used = "PostgreSQL" if use_cache else "None"
    
        if use_cache:
            logging.debug(f"Checking cache for key: {cache_key}")
            cached_data = cache.get(cache_key)
            if cached_data:
                cached_params = cached_data.get('params', {})
                if cached_params == {'start': start_timeframe, 'end': end_timeframe, 'frame': frame, 'group_by': group_by}:
                    data = cached_data["data"]
                    logging.debug(f"Cache hit for key: {cache_key}")
                    # Set cache_used to Redis if we hit Redis cache
                    cache_used = "Redis"
                    if group_by == "monthly":
                        data = [entry for entry in data if (start_timeframe is None or entry["period"] >= f"{start_timeframe.year}-{start_timeframe.month:02d}") and (end_timeframe is None or entry["period"] <= f"{end_timeframe.year}-{end_timeframe.month:02d}")]
                    elif group_by == "daily":
                        data = [entry for entry in data if (start_timeframe is None or entry["created_at"].date() >= start_timeframe) and (end_timeframe is None or entry["created_at"].date() <= end_timeframe)]

                    return JsonResponse({
                        "cache_used": cache_used,
                        "cache": cache_key,
                        "count": len(data),
                        "data": data
                    }, status=200)
                else:
                    logging.debug(f"Cache miss for key: {cache_key}, params do not match.")
            else:
                logging.debug(f"Cache miss for key: {cache_key}, no data found.")

        # Query the database if data is not in cache
        current_record_count = table_model.objects.count()
        latest_record = table_model.objects.aggregate(last_updated=Max("created_at"))

        cached_count_data = cache.get(count_cache_key)
        if cached_count_data:
            cached_count, cached_latest = cached_count_data
            if cached_count == current_record_count and cached_latest == latest_record["last_updated"]:
                logging.debug("Cache count and latest record are up-to-date. No need to refresh cache.")
            else:
                logging.debug("Cache is outdated, deleting existing cache.")
                cache.delete(cache_key)

        queryset = table_model.objects.all()

        # สำหรับกรณี 1d ที่อาจต้องแสดงข้อมูลล่าสุดแทนหากไม่มีข้อมูลของวันนี้
        if frame == "1d" and show_latest_only:
            # ลองค้นหาข้อมูลของวันนี้ก่อน
            today_data = queryset.filter(created_at__date=end_timeframe).order_by('-created_at')
            
            if today_data.exists():
                # ถ้ามีข้อมูลของวันนี้ ให้ใช้ข้อมูลเฉพาะวันนี้
                queryset = today_data
            else:
                # ถ้าไม่มีข้อมูลของวันนี้ ให้ใช้ข้อมูลล่าสุดแทน โดยเรียงตามวันที่จากล่าสุดไปเก่าสุด
                latest_record = queryset.order_by('-created_at').first()
                
                if latest_record:
                    # ถ้ามีข้อมูลล่าสุด กำหนดให้ start_timeframe และ end_timeframe เป็นวันที่ของข้อมูลล่าสุด
                    start_timeframe = latest_record.created_at.date()
                    end_timeframe = latest_record.created_at.date()
                    queryset = queryset.filter(created_at__date=start_timeframe)
                else:
                    # ถ้าไม่มีข้อมูลเลย (ไม่น่าเกิดกรณีนี้) ให้คืนค่าเป็น queryset ว่าง
                    queryset = queryset.none()
        else:
            # กรองตามช่วงเวลาเฉพาะเมื่อไม่ใช่กรณีที่ต้องการเพียงข้อมูลล่าสุด
            if start_timeframe:
                queryset = queryset.filter(created_at__date__gte=start_timeframe)
            
            # ตรวจสอบว่ามีข้อมูลในช่วงวันที่สิ้นสุดหรือไม่
            if end_timeframe and queryset.filter(created_at__date__lte=end_timeframe).exists():
                queryset = queryset.filter(created_at__date__lte=end_timeframe)
            elif end_timeframe:
                # ถ้าไม่มีข้อมูลในวันที่ต้องการ หาข้อมูลวันที่ใกล้เคียงที่สุด
                # แก้ไขส่วนนี้ให้เรียงลำดับตาม created_at จากใหม่ไปเก่า
                closest_date = table_model.objects.filter(created_at__date__lt=end_timeframe).order_by('-created_at').first()
                if closest_date:
                    end_timeframe = closest_date.created_at.date()
                    queryset = queryset.filter(created_at__date__lte=end_timeframe)

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
                    "max_price": entry["max_price"],
                }
                for entry in queryset
            ]

        else:
            return JsonResponse({"error": "Invalid 'group_by' parameter. Use 'daily' or 'monthly'."}, status=400)

        # Save new data to cache
        if use_cache:
            logging.debug(f"Saving new data to cache with key: {cache_key}")
            cache.set(count_cache_key, (current_record_count, latest_record["last_updated"]), timeout=cache_time)
            cache.set(cache_key, {"data": data, "count": len(data), "params": {'start': start_timeframe, 'end': end_timeframe, 'frame': frame, 'group_by': group_by}}, timeout=cache_time)

        return JsonResponse({
            "cache_used": cache_used,
            "cache": cache_key,
            "count": len(data),
            "data": data
        })

    except ValueError:
        return JsonResponse({"error": "Invalid date format. Use 'dd-mm-yyyy'."}, status=400)
    except LookupError:
        return JsonResponse({"error": f"Model '{table_name}' does not exist in app 'finnomenaGold'."}, status=400)
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