import pytz
from datetime import datetime, timezone
from data.models import USDTHB
from .getdatausdthb import get_data_usdthb

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