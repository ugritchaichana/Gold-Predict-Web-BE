import cloudscraper
import time
import random
import requests
from datetime import timedelta, datetime, timezone
from django.http import JsonResponse
import json
from .models import USDTHB, GoldTH
from django.views.decorators.http import require_GET, require_POST
import pytz

MAX_ITEMS = 5000
RESOLUTION_MINUTES = 60
SECONDS_PER_ITEM = RESOLUTION_MINUTES * 60
MAX_DELTA_SECONDS = MAX_ITEMS * SECONDS_PER_ITEM
MAX_DELTA = timedelta(seconds=MAX_DELTA_SECONDS)

def format_date(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + " +0700"

@require_GET
def create_data_set(request):
    try:
        select = request.GET.get('select', 'USDTHB').upper()
        start_str = request.GET.get('start', '')
        end_str = request.GET.get('end', '')
        local_tz = pytz.timezone('Asia/Bangkok')
        
        if not start_str:
            default_start = (datetime.now(local_tz) - timedelta(days=3))
            start_str = default_start.strftime('%d-%m-%y')
        else:
            default_start = None

        if not end_str:
            current_date = datetime.now(local_tz)
            end_str = current_date.strftime('%d-%m-%y')
            default_end = current_date
        else:
            default_end = None

        if not start_str or not end_str:
            return JsonResponse({
                "status": "error",
                "message": "Missing required parameters: 'start' and 'end'",
                "data": None
            }, status=400)

        try:
            start_dt = local_tz.localize(datetime.strptime(start_str, "%d-%m-%y").replace(
                hour=0, minute=0, second=0, microsecond=0))
            
            end_dt = local_tz.localize(datetime.strptime(end_str, "%d-%m-%y").replace(
                hour=23, minute=59, second=59, microsecond=0))
        except ValueError:
            return JsonResponse({
                "status": "error",
                "message": "Invalid date format. Please use 'dd-mm-yy'",
                "data": None
            }, status=400)

        start_ts = int(start_dt.astimezone(timezone.utc).timestamp())
        end_ts = int(end_dt.astimezone(timezone.utc).timestamp())

        if select == 'USDTHB':
            data = create_data_usdthb(start_ts, end_ts)
        elif select == 'GOLDTH':
            data = create_data_goldth(start_ts, end_ts)
        elif select == 'GOLDUS':
            data = "test GOLDUS"
        else:
            return JsonResponse({
                "status": "error",
                "message": "Currency not supported",
                "data": None
            }, status=400)

        return JsonResponse({
            "status": "success",
            "data": data,
            "start_date": format_date(start_dt),
            "end_date": format_date(end_dt),
            "default_dates_used": {
                "start": format_date(default_start) if default_start else None,
                "end": format_date(default_end) if default_end else None
            },
        }, status=200)

    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return JsonResponse({
            "status": "error",
            "message": "Internal server error",
            "data": None
        }, status=500)

@require_GET
def get_data(request):
    try:
        select = request.GET.get('select', '').upper()
        start_str = request.GET.get('start', '')
        end_str = request.GET.get('end', '')
        display = request.GET.get('display', '')
        local_tz = pytz.timezone('Asia/Bangkok')
        
        if not start_str:
            default_start = (datetime.now(local_tz) - timedelta(days=3))
            start_str = default_start.strftime('%d-%m-%y')
        else:
            default_start = None

        if not end_str:
            current_date = datetime.now(local_tz)
            end_str = current_date.strftime('%d-%m-%y')
            default_end = current_date
        else:
            default_end = None

        if not start_str or not end_str:
            return JsonResponse({
                "status": "error",
                "message": "Missing required parameters: 'start' and 'end'",
                "data": None
            }, status=400)
        
        try:
            start_dt = local_tz.localize(datetime.strptime(start_str, "%d-%m-%y").replace(
                hour=0, minute=0, second=0, microsecond=0))
            
            end_dt = local_tz.localize(datetime.strptime(end_str, "%d-%m-%y").replace(
                hour=23, minute=59, second=59, microsecond=0))
        except ValueError:
            return JsonResponse({
                "status": "error",
                "message": "Invalid date format. Please use 'dd-mm-yy'",
                "data": None
            }, status=400)
        
        start_ts = int(start_dt.astimezone(timezone.utc).timestamp())
        end_ts = int(end_dt.astimezone(timezone.utc).timestamp())

        if select == 'USDTHB':
            data = USDTHB.objects.filter(timestamp__gte=start_ts, timestamp__lte=end_ts).values()
        elif select in ('GOLDTH'):
            data = GoldTH.objects.filter(timestamp__gte=start_ts, timestamp__lte=end_ts).values()
        else:
            return JsonResponse({
                "status": "error",
                "message": "Currency not supported",
                "data": None
            }, status=400)
        
        return JsonResponse({
            "status": "success",
            "data": list(data),
            "start_date": format_date(start_dt),
            "end_date": format_date(end_dt),
            "default_dates_used": {
                "start": format_date(default_start) if default_start else None,
                "end": format_date(default_end) if default_end else None
            }
        }, status=200)
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": "Internal server error",
            "data": None
        }, status=500)

def get_data_usdthb(start_ts, end_ts):
    start_dt = datetime.utcfromtimestamp(start_ts).replace(tzinfo=timezone.utc)
    end_dt = datetime.utcfromtimestamp(end_ts).replace(tzinfo=timezone.utc)
    
    if start_dt > end_dt:
        raise ValueError("Start time cannot be greater than end time.")

    current_start = start_dt
    all_data = []
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
    ]

    while current_start < end_dt:
        current_end = min(current_start + MAX_DELTA, end_dt)
        
        url = (
            f'https://tvc4.investing.com/57c182657e622fb4e391a1c95dbc2589/'
            f'1742541167/1/1/8/history?symbol=147&resolution={RESOLUTION_MINUTES}&'
            f'from={int(current_start.timestamp())}&to={int(current_end.timestamp())}'
        )

        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Referer': 'https://www.investing.com/currencies/usd-thb',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
        
        time.sleep(random.uniform(1, 3))
        
        scraper = cloudscraper.create_scraper()
        response = scraper.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        parsed_data = response.json()
        
        if parsed_data.get('s') != 'ok':
            raise RuntimeError(f"API error: {parsed_data.get('s', 'Unknown error')}")
        
        try:
            timestamps = parsed_data["t"]
            close_prices = parsed_data["c"]
            open_prices = parsed_data["o"]
            high_prices = parsed_data["h"]
            low_prices = parsed_data["l"]
        except KeyError as e:
            raise RuntimeError(f"Unexpected response format: Missing key {e}") from e

        for i in range(len(timestamps)):
            all_data.append({
                "timestamp": timestamps[i],
                "date": datetime.utcfromtimestamp(timestamps[i]).strftime('%d-%m-%Y'),
                "close": close_prices[i],
                "open": open_prices[i],
                "high": high_prices[i],
                "low": low_prices[i]
            })

        current_start = current_end

    return all_data

def create_data_usdthb(start, end):
    data = get_data_usdthb(start, end)
    
    api_timestamps = [item["timestamp"] for item in data]
    
    existing_timestamps = set(USDTHB.objects.filter(
        timestamp__in=api_timestamps
    ).values_list('timestamp', flat=True))
    
    processed_data = []
    for item in data:
        timestamp = item["timestamp"]
        
        if timestamp in existing_timestamps:
            continue
            
        dt = datetime.utcfromtimestamp(timestamp).replace(tzinfo=timezone.utc)
        tz = pytz.timezone("Asia/Bangkok")
        dt_bangkok = dt.astimezone(tz)
        
        processed_item = {
            "timestamp": timestamp,
            "open": round(item["open"], 2),
            "close": round(item["close"], 2),
            "high": round(item["high"], 2),
            "low": round(item["low"], 2),
            "created_at": dt_bangkok.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + " +0700",
            "date": dt_bangkok.strftime("%d-%m-%y")
        }
        processed_data.append(USDTHB(**processed_item))
    
    if processed_data:
        USDTHB.objects.bulk_create(processed_data)
        return {"status": "success", "new_records": len(processed_data), "total_from_api": len(data)}
    return {"status": "no_new_data", "message": "All data already exists in database"}

def create_data_goldth(start, end):
    data = get_data_goldth(start, end)

    api_timestamps = [item["timestamp"] for item in data]

    existing_records = {record.timestamp: record for record in GoldTH.objects.filter(
        timestamp__in=api_timestamps
    )}

    processed_data = []
    for item in data:
        timestamp = item["timestamp"]

        if timestamp == 0:
            created_at = item.get("createdAt")
            if created_at:
                dt = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
                timestamp = int(dt.timestamp())
            else:
                continue

        dt = datetime.utcfromtimestamp(timestamp).replace(tzinfo=timezone.utc)
        tz = pytz.timezone("Asia/Bangkok")
        dt_bangkok = dt.astimezone(tz)

        try:
            new_data = {
                "timestamp": timestamp,
                "price": round(float(item.get("price", 0.0)), 2) if item.get("price") else 0.0,
                "bar_sell_price": round(float(item.get("barSellPrice", 0.0)), 2) if item.get("barSellPrice") else 0.0,
                "bar_price_change": round(float(item.get("barPriceChange", 0.0)), 2) if item.get("barPriceChange") else 0.0,
                "ornament_buy_price": round(float(item.get("ornamentBuyPrice", 0.0)), 2) if item.get("ornamentBuyPrice") else 0.0,
                "ornament_sell_price": round(float(item.get("ornamentSellPrice", 0.0)), 2) if item.get("ornamentSellPrice") else 0.0,
                "created_at": dt_bangkok,
                "created_time": dt_bangkok.strftime("%H:%M:%S"),
                "date": dt_bangkok.strftime("%d-%m-%y")
            }

            existing_record = existing_records.get(timestamp)
            if existing_record:
                for field, value in new_data.items():
                    if getattr(existing_record, field) != value:
                        setattr(existing_record, field, value)
                existing_record.save()
            else:
                processed_data.append(GoldTH(**new_data))

        except ValueError as e:
            print(f"Skipping invalid data: {item}, error: {e}")
            continue

    if processed_data:
        GoldTH.objects.bulk_create(processed_data)
        return {"status": "success", "new_records": len(processed_data), "total_from_api": len(data)}
    return {"status": "no_new_data", "message": "All data already exists in database"}

def get_data_goldth(start_str, end_str):
    print(f"check params start : {start_str} to end : {end_str}")
    
    if isinstance(start_str, int) or start_str.isdigit():
        start_date = datetime.utcfromtimestamp(int(start_str))
    else:
        start_date = datetime.strptime(start_str, '%d-%m-%y')

    if isinstance(end_str, int) or end_str.isdigit():
        end_date = datetime.utcfromtimestamp(int(end_str))
    else:
        end_date = datetime.strptime(end_str, '%d-%m-%y')
    
    all_data = []
    current_date = start_date
    print(f"start : {start_date} to end : {end_date} and current_date : {current_date}")
    
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        url = f'https://www.finnomena.com/fn3/api/gold/trader/history/list?date={date_str}'
        print(f"start : {date_str} to end : {end_date} URL : {url}")
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            if data.get('statusOK') and data['data'].get('success'):
                all_data.extend(data['data']['data'])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data for {date_str}: {e}")
        
        current_date += timedelta(days=1)
        print("current_date ++")
    return all_data


@require_GET
def delete_data(request):
    try:
        select = request.GET.get('select', 'USDTHB').upper()
        start_str = request.GET.get('start', '01-01-21')
        end_str = request.GET.get('end', datetime.now(pytz.timezone('Asia/Bangkok')).strftime('%d-%m-%y'))
        local_tz = pytz.timezone('Asia/Bangkok')

        if not start_str or not end_str:
            return JsonResponse({
                "status": "error",
                "message": "Missing required parameters: 'start' and 'end'",
                "data": None
            }, status=400)

        try:
            start_dt = local_tz.localize(datetime.strptime(start_str, "%d-%m-%y").replace(
                hour=0, minute=0, second=0, microsecond=0))
            
            end_dt = local_tz.localize(datetime.strptime(end_str, "%d-%m-%y").replace(
                hour=23, minute=59, second=59, microsecond=0))
        except ValueError:
            return JsonResponse({
                "status": "error",
                "message": "Invalid date format. Please use 'dd-mm-yy'",
                "data": None
            }, status=400)

        start_ts = int(start_dt.astimezone(pytz.utc).timestamp())
        end_ts = int(end_dt.astimezone(pytz.utc).timestamp())

        if select == 'USDTHB':
            deleted_count, _ = USDTHB.objects.filter(
                timestamp__gte=start_ts,
                timestamp__lte=end_ts
            ).delete()

            return JsonResponse({
                "status": "success",
                "message": f"Deleted {deleted_count} records",
                "start_date": start_dt.strftime('%Y-%m-%d %H:%M:%S %z'),
                "end_date": end_dt.strftime('%Y-%m-%d %H:%M:%S %z'),
                "deleted_count": deleted_count
            }, status=200)
        
        elif select == 'GOLDTH':
            deleted_count, _ = GoldTH.objects.filter(
                timestamp__gte=start_ts,
                timestamp__lte=end_ts
            ).delete()

            return JsonResponse({
                "status": "success",
                "message": f"Deleted {deleted_count} records",
                "start_date": start_dt.strftime('%Y-%m-%d %H:%M:%S %z'),
                "end_date": end_dt.strftime('%Y-%m-%d %H:%M:%S %z'),
                "deleted_count": deleted_count
            }, status=200)

        return JsonResponse({
            "status": "error",
            "message": "Currency not supported",
            "data": None
        }, status=400)

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": f"Internal server error: {str(e)}",
            "data": None
        }, status=500)