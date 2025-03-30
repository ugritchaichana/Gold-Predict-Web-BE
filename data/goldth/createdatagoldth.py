from .getdatagoldth import get_data_goldth
from datetime import datetime, timezone
import pytz
from data.models import GoldTH

def create_data_goldth(start, end):
    data = get_data_goldth(start, end)

    api_timestamps = [item["timestamp"] for item in data]

    existing_records = {record.timestamp: record for record in GoldTH.objects.filter(
        timestamp__in=api_timestamps
    )}

    processed_data = []
    for item in data:
        timestamp = item["timestamp"]

        if timestamp == 0:
            created_at = item.get("createdAt")
            if created_at:
                dt = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
                timestamp = int(dt.timestamp())
            else:
                continue

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

            existing_record = existing_records.get(timestamp)
            if existing_record:
                for field, value in new_data.items():
                    if getattr(existing_record, field) != value:
                        setattr(existing_record, field, value)
                existing_record.save()
            else:
                processed_data.append(GoldTH(**new_data))

        except ValueError as e:
            print(f"Skipping invalid data: {item}, error: {e}")
            continue

    if processed_data:
        GoldTH.objects.bulk_create(processed_data)
        return {"status": "success", "new_records": len(processed_data), "total_from_api": len(data)}
    return {"status": "no_new_data", "message": "All data already exists in database"}