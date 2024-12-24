import requests
from django.http import JsonResponse
from django.apps import apps  # ใช้สำหรับดึงโมเดลตามชื่อ
from django.db import transaction

def fetch_gold_data(request):
    # รับพารามิเตอร์ contry_table
    contry_table_name = request.GET.get('contry_table')  # บังคับให้ต้องระบุ
    if not contry_table_name:
        return JsonResponse({"error": "Missing 'contry_table' parameter."}, status=400)

    # รับพารามิเตอร์เพิ่มเติม
    period = request.GET.get('period', 'MAX')  # Default period: MAX
    sampling = request.GET.get('sampling', '0')  # Default sampling: 0
    start_timeframe = request.GET.get('startTimeframe', '')  # Default startTimeframe: None

    try:
        # ดึง model class จาก string
        contry_table = apps.get_model('finnomenaGold', contry_table_name)

        # สร้าง URL API พร้อมพารามิเตอร์
        url = (
            f"https://www.finnomena.com/fn3/api/gold/trader/history/graph?"
            f"period={period}&sampling={sampling}&startTimeframe={start_timeframe}"
        )

        # Request ข้อมูลจาก API
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json().get("data", [])
            bulk_data = []

            # ดึงค่าที่มีอยู่ในฐานข้อมูลเพื่อลดการ query ซ้ำซ้อน
            existing_timestamps = set(contry_table.objects.values_list("timestamp", flat=True))

            for item in data:
                if item["timestamp"] not in existing_timestamps:
                    bulk_data.append(
                        contry_table(
                            timestamp=item["timestamp"],
                            created_at=item["createdAt"],
                            created_time=item["createdTime"],
                            bar_buy_price=item["barBuyPrice"],
                            bar_sell_price=item["barSellPrice"],
                            bar_price_change=item["barPriceChange"],
                            ornament_buy_price=item["ornamentBuyPrice"],
                            ornament_sell_price=item["ornamentSellPrice"],
                            created_date_time=item["createdDateTime"],
                        )
                    )

            # ใช้ bulk_create เพื่อบันทึกข้อมูลทีละ batch
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
    # รับพารามิเตอร์ contry_table
    contry_table_name = request.GET.get('contry_table')  # บังคับให้ต้องระบุ
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
    # รับพารามิเตอร์ contry_table
    contry_table_name = request.GET.get('contry_table')  # บังคับให้ต้องระบุ
    if not contry_table_name:
        return JsonResponse({"error": "Missing 'contry_table' parameter."}, status=400)

    # รับพารามิเตอร์ช่วงเวลา
    start_timeframe = request.GET.get('startTimeframe', None)  # เริ่มต้น
    end_timeframe = request.GET.get('endTimeframe', None)  # สิ้นสุด

    try:
        contry_table = apps.get_model('finnomenaGold', contry_table_name)

        # กรองข้อมูลตามช่วงเวลาที่ระบุ
        queryset = contry_table.objects.all()
        if start_timeframe:
            queryset = queryset.filter(created_date_time__gte=start_timeframe)
        if end_timeframe:
            queryset = queryset.filter(created_date_time__lte=end_timeframe)

        # แปลงข้อมูลเป็น JSON
        data = list(queryset.values())
        return JsonResponse({"data": data, "count": len(data)})
    except LookupError:
        return JsonResponse({"error": f"Model '{contry_table_name}' does not exist in app 'finnomenaGold'."}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
