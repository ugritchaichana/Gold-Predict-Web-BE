# ปรับปรุง Caching Strategy สำหรับ Free Tier

## การลด Cache Dependency

### 1. ใช้ Smart Caching
```python
# ตัวอย่างใน views.py
from django.core.cache import cache
from django.conf import settings
import hashlib

def get_gold_price_cached(date_range):
    # สร้าง cache key ที่ unique
    cache_key = f"gold_price_{hashlib.md5(str(date_range).encode()).hexdigest()}"
    
    # ลองหาใน cache ก่อน
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    
    # ถ้าไม่มีใน cache ค่อยดึงจาก database
    data = fetch_gold_price_from_db(date_range)
    
    # เก็บใน cache นาน 1 ชั่วโมง
    cache.set(cache_key, data, 3600)
    
    return data
```

### 2. Cache ที่สำคัญเท่านั้น
- ราคาทองคำล่าสุด (cache 5 นาทีเท่านั้น)
- การพยากรณ์ (cache 1 ชั่วโมง)
- อัตราแลกเปลี่ยน (cache 30 นาที)
- ไม่ cache ข้อมูลที่เปลี่ยนแปลงบ่อย

### 3. ใช้ ETags สำหรับ Browser Cache
```python
# ใน views.py
from django.views.decorators.http import etag

def etag_func(request, *args, **kwargs):
    return hashlib.md5(f"gold_data_{timezone.now().hour}".encode()).hexdigest()

@etag(etag_func)
def gold_api_view(request):
    # Browser จะ cache ข้อมูลเป็นชั่วโมง
    pass
```

### 4. Database Query Optimization
- ใช้ select_related() และ prefetch_related()
- เพิ่ม database index
- ใช้ pagination สำหรับข้อมูลจำนวนมาก
