from .getdatagoldth import get_data_goldth
from datetime import datetime, timezone, timedelta
import pytz
from data.models import GoldTH
import gc

def create_data_goldth(start=None, end=None):
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
        
        data = get_data_goldth(start, end)

        # รวบรวม created_at จากข้อมูล API
        api_created_dates = []
        for item in data:
            created_at = item.get("createdAt")
            if created_at:
                api_created_dates.append(created_at)

        # ดึงข้อมูลที่มีอยู่แล้วในฐานข้อมูลตาม created_at
        existing_records = {}
        # แปลง created_at จาก string เป็น datetime object สำหรับแต่ละรายการใน api_created_dates
        created_at_datetimes = []
        for date_str in api_created_dates:
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                tz = pytz.timezone("Asia/Bangkok")
                dt_bangkok = dt.astimezone(tz)
                created_at_datetimes.append(dt_bangkok)
            except ValueError:
                continue

        # ดึงข้อมูลเก่าจาก DB ที่มี created_at ตรงกับข้อมูลที่จะนำเข้า
        if created_at_datetimes:
            for record in GoldTH.objects.filter(created_at__in=created_at_datetimes):
                existing_records[record.created_at] = record

        processed_data = []
        for item in data:
            timestamp = item["timestamp"]
            created_at_str = item.get("createdAt")

            if timestamp == 0 and not created_at_str:
                continue

            # แปลง created_at
            if created_at_str:
                dt = datetime.strptime(created_at_str, "%Y-%m-%dT%H:%M:%SZ")
                dt = dt.replace(tzinfo=timezone.utc)
                if timestamp == 0:
                    timestamp = int(dt.timestamp())
            else:
                dt = datetime.utcfromtimestamp(timestamp).replace(tzinfo=timezone.utc)
            
            tz = pytz.timezone("Asia/Bangkok")
            dt_bangkok = dt.astimezone(tz)

            try:
                new_data = {
                    "timestamp": timestamp,
                    "price": round(float(item.get("barBuyPrice", 0.0)), 2) if item.get("barBuyPrice") else 0.0,
                    "bar_sell_price": round(float(item.get("barSellPrice", 0.0)), 2) if item.get("barSellPrice") else 0.0,
                    "bar_price_change": round(float(item.get("barPriceChange", 0.0)), 2) if item.get("barPriceChange") else 0.0,
                    "ornament_buy_price": round(float(item.get("ornamentBuyPrice", 0.0)), 2) if item.get("ornamentBuyPrice") else 0.0,
                    "ornament_sell_price": round(float(item.get("ornamentSellPrice", 0.0)), 2) if item.get("ornamentSellPrice") else 0.0,
                    "created_at": dt_bangkok,
                    "created_time": dt_bangkok.strftime("%H:%M:%S"),
                    "date": dt_bangkok.strftime("%d-%m-%y")
                }

                # ตรวจสอบข้อมูลซ้ำโดยใช้ created_at แทน timestamp
                existing_record = existing_records.get(dt_bangkok)
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
                    processed_data.append(GoldTH(**new_data))

            except ValueError as e:
                print(f"Skipping invalid data: {item}, error: {e}")
                continue

        result = {}
        if processed_data:
            GoldTH.objects.bulk_create(processed_data)
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
        del data, api_created_dates, existing_records, created_at_datetimes, processed_data
        gc.collect()  # เรียก garbage collector เพื่อเคลียร์หน่วยความจำ
        
        return result
        
    except Exception as e:
        # เคลียร์ตัวแปรและคืนค่าข้อผิดพลาด
        gc.collect()
        return {"status": "error", "message": str(e)}