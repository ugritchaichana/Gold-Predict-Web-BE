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
def daily_data(request):
    try:
        local_tz = pytz.timezone('Asia/Bangkok')
        current_date = datetime.now(local_tz)
        three_days_ago = current_date - timedelta(days=3)
        
        start_ts = int(three_days_ago.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc).timestamp())
        end_ts = int(current_date.replace(hour=23, minute=59, second=59, microsecond=0).astimezone(timezone.utc).timestamp())
        
        usdthb_data = create_data_usdthb(start_ts, end_ts)
        goldth_data = create_data_goldth(start_ts, end_ts)
        goldus_data = create_data_goldus(start_ts, end_ts)
        
        return JsonResponse({
            "status": "success",
            "message": "Daily data updated successfully",
            "data": {
                "USDTHB": usdthb_data,
                "GOLDTH": goldth_data,
                "GOLDUS": goldus_data
            },
            "start_date": format_date(three_days_ago),
            "end_date": format_date(current_date)
        }, status=200)
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": f"Failed to update daily data: {str(e)}",
            "data": None
        }, status=500)

@require_GET
def set_database(request):
    try:
        select = request.GET.get('select', '').upper()
        local_tz = pytz.timezone('Asia/Bangkok')
        current_date = datetime.now(local_tz)
        
        # กำหนดวันเริ่มต้นเป็น 1 ม.ค. 2005 ถ้าไม่มีข้อมูลในฐานข้อมูล
        default_start = local_tz.localize(datetime.strptime("01-01-05", "%d-%m-%y").replace(
            hour=0, minute=0, second=0, microsecond=0))
        default_start_ts = int(default_start.astimezone(timezone.utc).timestamp())
        
        end_dt = current_date.replace(hour=23, minute=59, second=59, microsecond=0)
        end_ts = int(end_dt.astimezone(timezone.utc).timestamp())
        
        results = {
            "status": "success",
            "message": "Database check and fill completed",
            "data_created": []
        }
        
        # ฟังก์ชันสำหรับการสร้างข้อมูลเป็นช่วง
        def create_data_in_chunks(data_type, start_ts, end_ts, chunk_days=30):
            created_data = []
            current_ts = start_ts
            
            while current_ts < end_ts:
                chunk_end_ts = min(current_ts + (chunk_days * 24 * 60 * 60), end_ts)
                
                if data_type == 'USDTHB':
                    chunk_data = create_data_usdthb(current_ts, chunk_end_ts)
                elif data_type == 'GOLDTH':
                    chunk_data = create_data_goldth(current_ts, chunk_end_ts)
                elif data_type == 'GOLDUS':
                    chunk_data = create_data_goldus(current_ts, chunk_end_ts)
                
                if chunk_data:
                    created_data.extend(chunk_data)
                
                current_ts = chunk_end_ts + 1
            
            return created_data
        
        # ฟังก์ชันสำหรับหาช่วงวันที่ขาดหายไป
        def find_missing_date_ranges(data_type, model_class):
            all_records = model_class.objects.all().order_by('timestamp')
            
            if not all_records.exists():
                # ไม่มีข้อมูลเลย สร้างตั้งแต่ 2005 ถึงปัจจุบัน
                results["data_created"].append({
                    "type": data_type,
                    "range": f"No data found, creating from {default_start.strftime('%d-%m-%Y')} to {current_date.strftime('%d-%m-%Y')}"
                })
                return create_data_in_chunks(data_type, default_start_ts, end_ts)
            
            # มีข้อมูลอยู่แล้ว ตรวจสอบช่วงที่ขาดหาย
            first_record = all_records.first()
            last_record = all_records.last()
            
            # ถ้าข้อมูลแรกสุดไม่ใช่ 2005 ให้สร้างข้อมูลเพิ่ม
            if first_record.timestamp > default_start_ts:
                results["data_created"].append({
                    "type": data_type,
                    "range": f"Missing early data, creating from {default_start.strftime('%d-%m-%Y')} to {datetime.fromtimestamp(first_record.timestamp).strftime('%d-%m-%Y')}"
                })
                create_data_in_chunks(data_type, default_start_ts, first_record.timestamp - 1)
            
            # ตรวจสอบช่องว่างในข้อมูล
            missing_data = []
            prev_timestamp = None
            
            for record in all_records:
                if prev_timestamp is not None:
                    # ตรวจสอบว่ามีช่องว่างมากกว่า 1 วันหรือไม่
                    if record.timestamp - prev_timestamp > 24 * 60 * 60:  # 1 วัน
                        start_date = datetime.fromtimestamp(prev_timestamp, local_tz) + timedelta(seconds=1)
                        end_date = datetime.fromtimestamp(record.timestamp, local_tz) - timedelta(seconds=1)
                        
                        results["data_created"].append({
                            "type": data_type,
                            "range": f"Missing data from {start_date.strftime('%d-%m-%Y')} to {end_date.strftime('%d-%m-%Y')}"
                        })
                        
                        missing_data.extend(create_data_in_chunks(data_type, 
                            int(start_date.astimezone(timezone.utc).timestamp()), 
                            int(end_date.astimezone(timezone.utc).timestamp())))
                
                prev_timestamp = record.timestamp
            
            # ตรวจสอบข้อมูลล่าสุดถึงปัจจุบัน
            if last_record.timestamp < end_ts - (24 * 60 * 60):  # น้อยกว่าปัจจุบัน 1 วัน
                start_date = datetime.fromtimestamp(last_record.timestamp, local_tz) + timedelta(seconds=1)
                
                results["data_created"].append({
                    "type": data_type,
                    "range": f"Missing recent data, creating from {start_date.strftime('%d-%m-%Y')} to {current_date.strftime('%d-%m-%Y')}"
                })
                
                missing_data.extend(create_data_in_chunks(data_type, 
                    int(start_date.astimezone(timezone.utc).timestamp()), 
                    end_ts))
            
            return missing_data
        
        # ทำงานตามประเภทข้อมูลที่เลือก
        if not select or select == 'ALL':
            # ดำเนินการกับทุกประเภทข้อมูล
            usdthb_data = find_missing_date_ranges('USDTHB', USDTHB)
            goldth_data = find_missing_date_ranges('GOLDTH', GoldTH)
            goldus_data = find_missing_date_ranges('GOLDUS', GoldUS)
            
            results["data"] = {
                "USDTHB": len(usdthb_data),
                "GOLDTH": len(goldth_data),
                "GOLDUS": len(goldus_data)
            }
        elif select == 'USDTHB':
            data = find_missing_date_ranges('USDTHB', USDTHB)
            results["data"] = {"USDTHB": len(data)}
        elif select == 'GOLDTH':
            data = find_missing_date_ranges('GOLDTH', GoldTH)
            results["data"] = {"GOLDTH": len(data)}
        elif select == 'GOLDUS':
            data = find_missing_date_ranges('GOLDUS', GoldUS)
            results["data"] = {"GOLDUS": len(data)}
        else:
            return JsonResponse({
                "status": "error",
                "message": "Currency not supported. Use 'USDTHB', 'GOLDTH', 'GOLDUS', or leave empty for all."
            }, status=400)
        
        return JsonResponse(results, status=200)
        
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": f"Failed to set database: {str(e)}",
            "data": None
        }, status=500)

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
        timeframe = request.GET.get('timeframe', '').lower()
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
            queryset = USDTHB.objects.filter(timestamp__gte=start_ts, timestamp__lte=end_ts)
        elif select == 'GOLDTH':
            queryset = GoldTH.objects.filter(timestamp__gte=start_ts, timestamp__lte=end_ts)
        elif select == 'GOLDUS':
            queryset = GoldUS.objects.filter(timestamp__gte=start_ts, timestamp__lte=end_ts)
        else:
            return JsonResponse({
                "status": "error",
                "message": "Currency not supported",
                "data": None
            }, status=400)
        
        if timeframe:
            processed_data = process_data_by_timeframe(list(queryset.values()), timeframe, local_tz)
        else:
            processed_data = list(queryset.values())
        
        if display.lower() == 'chart':
            formatted_data = format_data_for_chart(processed_data, select, timeframe)
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
                "data": processed_data,
                "start_date": format_date(start_dt),
                "end_date": format_date(end_dt),
                "default_dates_used": {
                    "start": format_date(default_start) if default_start else None,
                    "end": format_date(default_end) if default_end else None
                }
            }
        return JsonResponse(response_data, status=200)
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": f"Internal server error: {str(e)}",
            "data": None
        }, status=500)

def process_data_by_timeframe(data, timeframe, tz):
    if not data:
        return []
    
    data = sorted(data, key=lambda x: x['timestamp'])
    
    if timeframe == 'day':
        processed_data = []
        day_groups = {}
        
        for item in data:
            dt = datetime.fromtimestamp(item['timestamp'], tz)
            date_key = dt.strftime('%Y-%m-%d')
            
            if date_key not in day_groups:
                day_groups[date_key] = []
            
            day_groups[date_key].append(item)
        
        for date_key in day_groups:
            day_data = day_groups[date_key]
            if len(day_data) > 0:
                latest_item = day_data[-1].copy()
                for record in day_data:
                    if 'high' in record and ('high' not in latest_item or record['high'] > latest_item['high']):
                        latest_item['high'] = record['high']
                    if 'low' in record and ('low' not in latest_item or record['low'] < latest_item['low']):
                        latest_item['low'] = record['low']
                
                if 'open' in day_data[0]:
                    latest_item['open'] = day_data[0]['open']
                    
                processed_data.append(latest_item)
                
        return processed_data
    
    elif timeframe == 'week':
        processed_data = []
        week_groups = {}
        
        for item in data:
            dt = datetime.fromtimestamp(item['timestamp'], tz)
            year, week_num, _ = dt.isocalendar()
            week_key = f"{year}-W{week_num:02d}"
            
            if week_key not in week_groups:
                week_groups[week_key] = []
            
            week_groups[week_key].append(item)
        
        for week_key in week_groups:
            week_data = week_groups[week_key]
            if len(week_data) > 0:
                latest_item = week_data[-1].copy()
                for record in week_data:
                    if 'high' in record and ('high' not in latest_item or record['high'] > latest_item['high']):
                        latest_item['high'] = record['high']
                    if 'low' in record and ('low' not in latest_item or record['low'] < latest_item['low']):
                        latest_item['low'] = record['low']
                
                if 'open' in week_data[0]:
                    latest_item['open'] = week_data[0]['open']
                    
                processed_data.append(latest_item)
                
        return processed_data
    
    elif timeframe == 'month':
        processed_data = []
        month_groups = {}
        
        for item in data:
            dt = datetime.fromtimestamp(item['timestamp'], tz)
            month_key = dt.strftime('%Y-%m')
            
            if month_key not in month_groups:
                month_groups[month_key] = []
            
            month_groups[month_key].append(item)
        
        for month_key in month_groups:
            month_data = month_groups[month_key]
            if len(month_data) > 0:
                latest_item = month_data[-1].copy()
                for record in month_data:
                    if 'high' in record and ('high' not in latest_item or record['high'] > latest_item['high']):
                        latest_item['high'] = record['high']
                    if 'low' in record and ('low' not in latest_item or record['low'] < latest_item['low']):
                        latest_item['low'] = record['low']
                
                if 'open' in month_data[0]:
                    latest_item['open'] = month_data[0]['open']
                    
                processed_data.append(latest_item)
                
        return processed_data
    
    elif timeframe == 'quarter':
        processed_data = []
        quarter_groups = {}
        
        for item in data:
            dt = datetime.fromtimestamp(item['timestamp'], tz)
            quarter = (dt.month - 1) // 3 + 1
            quarter_key = f"{dt.year}-Q{quarter}"
            
            if quarter_key not in quarter_groups:
                quarter_groups[quarter_key] = []
            
            quarter_groups[quarter_key].append(item)
        
        for quarter_key in quarter_groups:
            quarter_data = quarter_groups[quarter_key]
            if len(quarter_data) > 0:
                latest_item = quarter_data[-1].copy()
                for record in quarter_data:
                    if 'high' in record and ('high' not in latest_item or record['high'] > latest_item['high']):
                        latest_item['high'] = record['high']
                    if 'low' in record and ('low' not in latest_item or record['low'] < latest_item['low']):
                        latest_item['low'] = record['low']
                
                if 'open' in quarter_data[0]:
                    latest_item['open'] = quarter_data[0]['open']
                    
                processed_data.append(latest_item)
                
        return processed_data
    
    elif timeframe == 'year':
        processed_data = []
        year_groups = {}
        
        for item in data:
            dt = datetime.fromtimestamp(item['timestamp'], tz)
            year_key = str(dt.year)
            
            if year_key not in year_groups:
                year_groups[year_key] = []
            
            year_groups[year_key].append(item)
        
        for year_key in year_groups:
            year_data = year_groups[year_key]
            if len(year_data) > 0:
                latest_item = year_data[-1].copy()
                for record in year_data:
                    if 'high' in record and ('high' not in latest_item or record['high'] > latest_item['high']):
                        latest_item['high'] = record['high']
                    if 'low' in record and ('low' not in latest_item or record['low'] < latest_item['low']):
                        latest_item['low'] = record['low']
                
                if 'open' in year_data[0]:
                    latest_item['open'] = year_data[0]['open']
                    
                processed_data.append(latest_item)
                
        return processed_data
    
    return data

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