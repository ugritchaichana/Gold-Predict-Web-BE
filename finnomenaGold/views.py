import requests
from django.http import JsonResponse
from django.apps import apps
from django.db import transaction
from datetime import datetime

def fetch_gold_data(request):
    contry_table_name = request.GET.get('contry_table')
    if not contry_table_name:
        return JsonResponse({"error": "Missing 'contry_table' parameter."}, status=400)

    period = request.GET.get('period', 'MAX')
    sampling = request.GET.get('sampling', '0')
    start_timeframe = request.GET.get('startTimeframe', '')

    try:
        contry_table = apps.get_model('finnomenaGold', contry_table_name)

        url = (
            f"https://www.finnomena.com/fn3/api/gold/trader/history/graph?"
            f"period={period}&sampling={sampling}&startTimeframe={start_timeframe}"
        )

        response = requests.get(url)
        if response.status_code == 200:
            data = response.json().get("data", [])
            bulk_data = []

            existing_timestamps = set(contry_table.objects.values_list("timestamp", flat=True))

            for item in data:
                if item["timestamp"] not in existing_timestamps:
                    if contry_table_name == 'Gold_TH':
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
            return JsonResponse({"error": "Failed to fetch data from API.", "status_code": response.status_code}, status=500)

    except LookupError:
        return JsonResponse({"error": f"Model '{contry_table_name}' does not exist in app 'finnomenaGold'."}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

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
    contry_table_name = request.GET.get('contry_table')
    if not contry_table_name:
        return JsonResponse({"error": "Missing 'contry_table' parameter."}, status=400)

    db_choice = request.GET.get('db_choice', None)
    if db_choice is None:
        return JsonResponse({"error": "Missing 'db_choice' parameter."}, status=400)

    table_mapping = {
        '0': 'Gold_TH',
        '1': 'Gold_US',
        '2': 'currency'
    }
    
    contry_table_name = table_mapping.get(db_choice)
    if not contry_table_name:
        return JsonResponse({"error": "Invalid 'db_choice' parameter value. Must be 0, 1, or 2."}, status=400)

    # รับพารามิเตอร์ช่วงเวลา
    start_timeframe = request.GET.get('startTimeframe', None)
    end_timeframe = request.GET.get('endTimeframe', None)

    try:
        contry_table = apps.get_model('finnomenaGold', contry_table_name)

        if start_timeframe:
            start_timeframe = datetime.strptime(start_timeframe, '%d-%m-%Y').strftime('%Y-%m-%d')
        if end_timeframe:
            end_timeframe = datetime.strptime(end_timeframe, '%d-%m-%Y').strftime('%Y-%m-%d')

        queryset = contry_table.objects.all()
        if start_timeframe:
            queryset = queryset.filter(created_at__gte=start_timeframe)
        if end_timeframe:
            queryset = queryset.filter(created_at__lte=end_timeframe)

        data = list(queryset.values('date', 'price'))

        return JsonResponse({"data": data, "count": len(data)})

    except LookupError:
        return JsonResponse({"error": f"Model '{contry_table_name}' does not exist in app 'finnomenaGold'."}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)