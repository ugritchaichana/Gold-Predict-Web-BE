from .getdatagoldus import get_data_goldus
from datetime import datetime, timezone
import pytz
from data.models import GoldUS

def create_data_goldus(start, end):
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
            # Update existing record if data differs
            for field, value in new_data.items():
                if getattr(existing_record, field) != value:
                    setattr(existing_record, field, value)
            existing_record.save()
        else:
            processed_data.append(GoldUS(**new_data))

    if processed_data:
        GoldUS.objects.bulk_create(processed_data)
        return {"status": "success", "new_records": len(processed_data), "total_from_api": len(data)}
    return {"status": "no_new_data", "message": "All data already exists in database"}