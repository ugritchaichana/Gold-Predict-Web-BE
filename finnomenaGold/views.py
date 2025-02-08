import time
import requests
from django.http import JsonResponse
from django.apps import apps
from datetime import datetime, timezone, timedelta
from django.db import transaction

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
    currentDateTime = datetime.now().strftime('%Y-%m-%d')
    url = f"https://www.finnomena.com/fn3/api/polygon/gold/spot/v2/aggs/ticker/C%3AXAUUSD/range/1/day/2005-01-01/{currentDateTime}"
    contry_table = apps.get_model('finnomenaGold', 'Gold_US')

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

    table_mapping = {
        '0': 'Gold_TH',
        '1': 'Gold_US',
        '2': 'currency'
    }
    
    table_name = table_mapping.get(db_choice)
    if not table_name:
        return JsonResponse({"error": "Invalid 'db_choice' parameter value. Must be 0, 1, or 2."}, status=400)

    start_timeframe = request.GET.get('startTimeframe', None)
    end_timeframe = request.GET.get('endTimeframe', None)

    try:
        table_model = apps.get_model('finnomenaGold', table_name)

        if start_timeframe:
            start_timeframe = datetime.strptime(start_timeframe, '%d-%m-%Y')
        if end_timeframe:
            end_timeframe = datetime.strptime(end_timeframe, '%d-%m-%Y')

        queryset = table_model.objects.all()

        if start_timeframe:
            queryset = queryset.filter(created_at__gte=start_timeframe)
            print('start_timeframe : ', start_timeframe)
        if end_timeframe:
            queryset = queryset.filter(created_at__lte=end_timeframe)
            print('end_timeframe : ', end_timeframe)
        
        print('queryset : ', queryset)

        data = list(queryset.values())

        return JsonResponse({"data": data, "count": len(data)})

    except LookupError:
        return JsonResponse({"error": f"Model '{table_name}' does not exist in app 'finnomenaGold'."}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
