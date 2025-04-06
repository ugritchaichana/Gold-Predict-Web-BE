from data.models import USDTHB
from django.db.models import Max
from datetime import datetime

def check_usdthb(action='do'):
    try:
        # ดึงข้อมูลทั้งหมดเรียงตามเวลา (timestamp)
        all_data = USDTHB.objects.all().order_by('timestamp')
        
        # ตรวจสอบการเรียงลำดับข้อมูล
        is_sorted = True
        unsorted_data = []
        prev_timestamp = None
        
        for data_point in all_data:
            if prev_timestamp is not None and data_point.timestamp < prev_timestamp:
                is_sorted = False
                unsorted_data.append({
                    "id": data_point.id,
                    "timestamp": data_point.timestamp,
                    "previous_timestamp": prev_timestamp
                })
            prev_timestamp = data_point.timestamp
        
        # ค้นหาและลบข้อมูลที่ซ้ำกันในช่วงเวลาเดียวกัน
        duplicates_removed = 0
        duplicate_data = []
        # สร้าง dictionary เก็บ timestamp และ id ล่าสุด
        latest_ids = {}
        
        # ดึงข้อมูลทั้งหมด
        all_records = USDTHB.objects.all()
        
        for record in all_records:
            ts = record.timestamp
            if ts in latest_ids:
                if record.id > latest_ids[ts]['id']:
                    # เก็บข้อมูลที่ซ้ำซ้อน
                    duplicate_data.append({
                        "id": latest_ids[ts]['id'],
                        "timestamp": ts,
                        "action": "remove_older"
                    })
                    
                    if action == 'do':
                        # ลบข้อมูลเก่าที่บันทึกไว้
                        USDTHB.objects.get(id=latest_ids[ts]['id']).delete()
                    
                    latest_ids[ts] = {'id': record.id}
                    duplicates_removed += 1
                else:
                    # เก็บข้อมูลที่ซ้ำซ้อน
                    duplicate_data.append({
                        "id": record.id,
                        "timestamp": ts,
                        "action": "remove_current"
                    })
                    
                    if action == 'do':
                        # ลบข้อมูลปัจจุบัน
                        record.delete()
                        
                    duplicates_removed += 1
            else:
                latest_ids[ts] = {'id': record.id}
        
        result = {
            "status": "success",
            "data_type": "USDTHB",
            "action": action,
            "is_sorted_correctly": is_sorted,
        }
        
        if action == 'show':
            result.update({
                "unsorted_data": unsorted_data if not is_sorted else [],
                "duplicate_data": duplicate_data,
                "total_records": USDTHB.objects.count(),
                "message": "Found issues that need to be fixed"
            })
        else:  # action == 'do'
            result.update({
                "duplicates_removed": duplicates_removed,
                "total_records": USDTHB.objects.count(),
                "message": "Data has been successfully checked and cleaned"
            })
            
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error occurred: {str(e)}"
        }
