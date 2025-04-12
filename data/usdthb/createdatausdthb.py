import pytz
from datetime import datetime, timezone, timedelta
from data.models import USDTHB
from .getdatausdthb import get_data_usdthb
import gc
import time
import random
import logging
import requests

# ตั้งค่า logging
logger = logging.getLogger(__name__)

def get_my_ip():
    """ฟังก์ชันสำหรับตรวจสอบ IP ภายนอกที่ใช้ในการเชื่อมต่ออินเทอร์เน็ต"""
    try:
        # ใช้หลายบริการเพื่อตรวจสอบ IP กรณีบริการหนึ่งล่ม
        ip_services = [
            "https://api.ipify.org",
            "https://ifconfig.me/ip",
            "https://icanhazip.com",
            "https://ipinfo.io/ip"
        ]
        
        for service in ip_services:
            try:
                response = requests.get(service, timeout=5)
                if response.status_code == 200:
                    ip = response.text.strip()
                    return ip
            except:
                continue
                
        return "ไม่สามารถตรวจสอบ IP ได้"
    except Exception as e:
        return f"ข้อผิดพลาดในการตรวจสอบ IP: {str(e)}"

def create_data_usdthb(start=None, end=None):
    try:
        # ตรวจสอบ IP ที่ใช้งานอยู่
        current_ip = get_my_ip()
        logger.info(f"เริ่มดึงข้อมูลด้วย IP: {current_ip}")
        print(f"กำลังดึงข้อมูลด้วย IP: {current_ip}")
        
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
                
        logger.info(f"Starting USDTHB data collection from {datetime.fromtimestamp(start)} to {datetime.fromtimestamp(end)}")
        
        # พยายามดึงข้อมูลซ้ำหลายครั้งหากมีปัญหา (แต่จริงๆ getdatausdthb.py มีกลไกลองใหม่ในตัวอยู่แล้ว)
        max_retries = 3
        retry_count = 0
        data = []
        
        while retry_count < max_retries and not data:
            try:
                # ดึงข้อมูลด้วย getdatausdthb ขั้นสูงที่ปรับปรุงแล้ว
                # ตรวจสอบ IP อีกครั้งก่อนการดึงข้อมูล (อาจมีการเปลี่ยนแปลงถ้าใช้ VPN)
                current_ip = get_my_ip()
                logger.info(f"ตรวจสอบ IP ก่อนส่งคำขอ (ครั้งที่ {retry_count+1}): {current_ip}")
                print(f"กำลังส่งคำขอด้วย IP (ครั้งที่ {retry_count+1}): {current_ip}")
                
                data = get_data_usdthb(start, end)
                if data:  # ถ้าได้ข้อมูลมาให้ออกจากลูป
                    logger.info(f"Successfully fetched {len(data)} data points with IP: {current_ip}")
                    print(f"ดึงข้อมูลสำเร็จ {len(data)} รายการด้วย IP: {current_ip}")
                    break
                else:
                    logger.warning(f"No data returned (attempt {retry_count+1}/{max_retries}) with IP: {current_ip}")
                    print(f"ไม่พบข้อมูล (ครั้งที่ {retry_count+1}/{max_retries}) จาก IP: {current_ip}")
            except Exception as e:
                retry_count += 1
                current_ip = get_my_ip()
                error_msg = f"Error fetching USDTHB data (attempt {retry_count}/{max_retries}): {str(e)}, IP: {current_ip}"
                logger.error(error_msg)
                print(error_msg)
                
                if retry_count < max_retries:
                    # รอสักพักก่อนลองใหม่ และสุ่มเวลารอเพื่อหลีกเลี่ยงการถูกบล็อก
                    sleep_time = random.uniform(5, 15)
                    logger.info(f"Retrying in {sleep_time:.2f} seconds...")
                    time.sleep(sleep_time)
                else:
                    logger.error("Max retries reached. Unable to fetch USDTHB data.")
        
        if not data:
            return {"status": "error", "message": "Failed to fetch data after multiple attempts", "ip_used": current_ip}
        
        # ดึงข้อมูลที่มีอยู่แล้วในฐานข้อมูล
        api_timestamps = [item["timestamp"] for item in data]
        
        # ดูว่ามี timestamps ซ้ำกันในข้อมูลที่ดึงมาหรือไม่
        duplicate_timestamps = set()
        unique_timestamps = set()
        
        for ts in api_timestamps:
            if ts in unique_timestamps:
                duplicate_timestamps.add(ts)
            else:
                unique_timestamps.add(ts)
        
        if duplicate_timestamps:
            logger.warning(f"Found {len(duplicate_timestamps)} duplicate timestamps in API data")
        
        # ดึงข้อมูลที่มีอยู่ในฐานข้อมูล
        existing_records = {record.timestamp: record for record in USDTHB.objects.filter(
            timestamp__in=api_timestamps
        )}
        
        logger.info(f"Found {len(existing_records)} existing records in database")
        
        # คำนวณข้อมูลที่ต้องเพิ่มใหม่
        processed_data = []
        updated_count = 0
        
        for item in data:
            timestamp = item["timestamp"]
            
            try:
                # แปลง timestamp เป็น datetime
                dt = datetime.utcfromtimestamp(timestamp).replace(tzinfo=timezone.utc)
                tz = pytz.timezone("Asia/Bangkok")
                dt_bangkok = dt.astimezone(tz)
                
                # สร้างข้อมูลใหม่
                new_data = {
                    "timestamp": timestamp,
                    "open": round(float(item["open"]), 2),
                    "close": round(float(item["close"]), 2),
                    "high": round(float(item["high"]), 2),
                    "low": round(float(item["low"]), 2),
                    "created_at": dt_bangkok.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + " +0700",
                    "date": dt_bangkok.strftime("%d-%m-%y")
                }
                
                # ตรวจสอบข้อมูลซ้ำโดยใช้ timestamp
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
                        updated_count += 1
                else:
                    processed_data.append(USDTHB(**new_data))
            except Exception as e:
                logger.error(f"Skipping invalid data: timestamp={timestamp}, error: {str(e)}")
                continue
        
        # บันทึกข้อมูลใหม่ทั้งหมด
        if processed_data:
            logger.info(f"Creating {len(processed_data)} new records")
            USDTHB.objects.bulk_create(processed_data)
        
        result = {}
        if processed_data or updated_count > 0:
            result = {
                "status": "success", 
                "new_records": len(processed_data),
                "updated_records": updated_count,
                "total_from_api": len(data),
                "unique_from_api": len(unique_timestamps),
                "time_range": {
                    "start": datetime.utcfromtimestamp(start).strftime('%d-%m-%y') if start else None,
                    "end": datetime.utcfromtimestamp(end).strftime('%d-%m-%y') if end else None
                },
                "ip_used": current_ip
            }
            logger.info(f"Success: {len(processed_data)} new records, {updated_count} updated records, IP: {current_ip}")
            print(f"สำเร็จ: เพิ่ม {len(processed_data)} รายการใหม่, อัปเดต {updated_count} รายการ, IP: {current_ip}")
        else:
            result = {
                "status": "no_new_data", 
                "message": "All data already exists in database",
                "time_range": {
                    "start": datetime.utcfromtimestamp(start).strftime('%d-%m-%y') if start else None,
                    "end": datetime.utcfromtimestamp(end).strftime('%d-%m-%y') if end else None
                },
                "ip_used": current_ip
            }
            logger.info(f"No new data to save, IP: {current_ip}")
            print(f"ไม่มีข้อมูลใหม่, IP: {current_ip}")
        
        # Clear all variables to prevent memory issues
        del data, api_timestamps, existing_records, processed_data
        gc.collect()  # เรียก garbage collector เพื่อเคลียร์หน่วยความจำ
        
        return result
        
    except Exception as e:
        current_ip = get_my_ip()
        error_msg = f"Unexpected error in create_data_usdthb: {str(e)}, IP: {current_ip}"
        logger.exception(error_msg)
        print(error_msg)
        # เคลียร์ตัวแปรและคืนค่าข้อผิดพลาด
        gc.collect()
        return {"status": "error", "message": str(e), "ip_used": current_ip}