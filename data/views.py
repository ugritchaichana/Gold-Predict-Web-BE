from django.views.decorators.http import require_GET
from django.http import JsonResponse
from datetime import datetime, timedelta, timezone
from data.usdthb.createdatausdthb import create_data_usdthb
from data.goldth.createdatagoldth import create_data_goldth
from data.goldus.createdatagoldus import create_data_goldus
from data.util.formatdate import format_date
from data.util.formatdataforchart import format_data_for_chart
from data.models import USDTHB, GoldTH, GoldUS
import pytz


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
            data = create_data_goldus(start_ts, end_ts)
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
        elif select == 'GOLDTH':
            data = GoldTH.objects.filter(timestamp__gte=start_ts, timestamp__lte=end_ts).values()
        elif select == 'GOLDUS':
            data = GoldUS.objects.filter(timestamp__gte=start_ts, timestamp__lte=end_ts).values()
        else:
            return JsonResponse({
                "status": "error",
                "message": "Currency not supported",
                "data": None
            }, status=400)
        
        if display.lower() == 'chart':
            formatted_data = format_data_for_chart(list(data), select)
            response_data = {
                "status": "success",
                "data": formatted_data,
                "start_date": format_date(start_dt),
                "end_date": format_date(end_dt),
                "default_dates_used": {
                    "start": format_date(default_start) if default_start else None,
                    "end": format_date(default_end) if default_end else None
                }
            }
        else:
            response_data = {
                "status": "success",
                "data": list(data),
                "start_date": format_date(start_dt),
                "end_date": format_date(end_dt),
                "default_dates_used": {
                    "start": format_date(default_start) if default_start else None,
                    "end": format_date(default_end) if default_end else None
                }
            }
            print("Response data:", response_data)  # Log response data
        return JsonResponse(response_data, status=200)
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": "Internal server error",
            "data": None
        }, status=500)

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
        elif select == 'GOLDTH':
            deleted_count, _ = GoldTH.objects.filter(
                timestamp__gte=start_ts,
                timestamp__lte=end_ts
            ).delete()
        elif select == 'GOLDUS':
            deleted_count, _ = GoldUS.objects.filter(
                timestamp__gte=start_ts,
                timestamp__lte=end_ts
            ).delete()
        else:
            return JsonResponse({
                "status": "error",
                "message": "Currency not supported",
                "data": None
            }, status=400)

        return JsonResponse({
            "status": "success",
            "message": f"Deleted {deleted_count} records",
            "start_date": start_dt.strftime('%Y-%m-%d %H:%M:%S %z'),
            "end_date": end_dt.strftime('%Y-%m-%d %H:%M:%S %z'),
            "deleted_count": deleted_count
        }, status=200)

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": f"Internal server error: {str(e)}",
            "data": None
        }, status=500)