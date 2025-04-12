from .getdatagoldus import get_data_goldus
from datetime import datetime, timezone, timedelta
import pytz
from data.models import GoldUS
import gc

def create_data_goldus(start=None, end=None):
    try:
        # กรณีไม่ระบุ start หรือ end ให้ใช้ช่วง 5 วันที่แล้วถึงวันปัจจุบัน
        if start is None or end is None:
            local_tz = pytz.timezone("Asia/Bangkok")
            current_date = datetime.now(local_tz)
            
            if end is None:
                end = int(current_date.timestamp())
            
            if start is None:
                # 5 วันย้อนหลังจากวันปัจจุบัน
                start_date = current_date - timedelta(days=5)
                start = int(start_date.timestamp())
        
        data = get_data_goldus(start, end)

        api_timestamps = [item["t"] // 1000 for item in data]  # Convert milliseconds to seconds

        existing_records = {record.timestamp: record for record in GoldUS.objects.filter(
            timestamp__in=api_timestamps
        )}

        processed_data = []
        for item in data:
            timestamp = item["t"] // 1000  # Convert milliseconds to seconds

            dt = datetime.utcfromtimestamp(timestamp).replace(tzinfo=timezone.utc)
            tz = pytz.timezone("Asia/Bangkok")
            dt_bangkok = dt.astimezone(tz)

            try:
                new_data = {
                    "timestamp": timestamp,
                    "price": round(item["o"], 2),
                    "close_price": round(item["c"], 2),
                    "high_price": round(item["h"], 2),
                    "low_price": round(item["l"], 2),
                    "volume": item["v"],
                    "volume_weight_avg": item["vw"],
                    "num_transactions": item["n"],
                    "created_at": dt_bangkok,
                    "date": dt_bangkok.strftime("%d-%m-%y")
                }

                existing_record = existing_records.get(timestamp)
                if existing_record:
                    # ถ้ามีข้อมูลอยู่แล้ว ตรวจสอบว่ามีค่าใดที่ไม่ตรงกันและอัปเดต
                    updated = False
                    for field, value in new_data.items():
                        if getattr(existing_record, field) != value:
                            setattr(existing_record, field, value)
                            updated = True
                    if updated:
                        existing_record.save()
                else:
                    processed_data.append(GoldUS(**new_data))
            except Exception as e:
                print(f"Skipping invalid data: {item}, error: {e}")
                continue

        result = {}
        if processed_data:
            GoldUS.objects.bulk_create(processed_data)
            result = {
                "status": "success", 
                "new_records": len(processed_data), 
                "total_from_api": len(data),
                "time_range": {
                    "start": datetime.utcfromtimestamp(start).strftime('%d-%m-%y') if start else None,
                    "end": datetime.utcfromtimestamp(end).strftime('%d-%m-%y') if end else None
                }
            }
        else:
            result = {
                "status": "no_new_data", 
                "message": "All data already exists in database",
                "time_range": {
                    "start": datetime.utcfromtimestamp(start).strftime('%d-%m-%y') if start else None,
                    "end": datetime.utcfromtimestamp(end).strftime('%d-%m-%y') if end else None
                }
            }
        
        # Clear all variables to prevent memory issues
        del data, api_timestamps, existing_records, processed_data
        gc.collect()  # เรียก garbage collector เพื่อเคลียร์หน่วยความจำ
        
        return result
        
    except Exception as e:
        # เคลียร์ตัวแปรและคืนค่าข้อผิดพลาด
        gc.collect()
        return {"status": "error", "message": str(e)}