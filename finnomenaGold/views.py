import time
import requests
from django.http import JsonResponse
from django.apps import apps
from datetime import datetime, timezone, timedelta
from django.db.models import Avg, Min, Max
from django.db import transaction
from django.core.cache import cache

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
    url = "https://www.finnomena.com/fn3/api/gold/trader/history/graph?period=MAX&sampling=0&startTimeframe="

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

import logging

# ตั้งค่า logging
logging.basicConfig(level=logging.DEBUG)

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

        if not start_timeframe and frame:
            if frame == "1d":
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
                return JsonResponse({"error": "Invalid 'frame' parameter."}, status=400)

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

        if start_timeframe:
            queryset = queryset.filter(created_at__date__gte=start_timeframe)
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
