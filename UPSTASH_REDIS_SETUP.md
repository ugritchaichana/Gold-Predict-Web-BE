# Setup Upstash Redis สำหรับ Render (ฟรี)

## ทำไมต้องใช้ External Redis?
- Render Free Tier ไม่รองรับ Redis service
- Database Cache ช้ามาก และมี uptime จำกัด (97 ชั่วโมง/เดือน)
- Upstash Redis ให้ 10,000 commands/day ฟรี

## ขั้นตอนการตั้งค่า Upstash Redis:

### 1. สร้าง Account ใน Upstash
1. ไปที่ https://upstash.com/
2. สมัครสมาชิกฟรี (ใช้ GitHub หรือ Email)
3. ยืนยัน Email

### 2. สร้าง Redis Database
1. คลิก "Create Database"
2. ตั้งชื่อ: `gold-predict-cache`
3. เลือก Region: `Singapore` (ใกล้ Render Singapore)
4. เลือก Type: `Regional` (ฟรี)
5. คลิก "Create"

### 3. คัดลอก Connection URL
1. ไปที่ Database ที่สร้าง
2. คลิกแท็บ "Details"
3. คัดลอก `UPSTASH_REDIS_REST_URL` หรือ `Redis URL`
4. ตัวอย่าง: `redis://default:xxxxx@singapore-redis.upstash.io:6379`

### 4. เพิ่ม Environment Variable ใน Render
1. ไปที่ Render Dashboard
2. เลือก Web Service ของคุณ
3. ไปที่แท็บ "Environment"
4. เพิ่ม Variable:
   ```
   Key: REDIS_URL
   Value: redis://default:xxxxx@singapore-redis.upstash.io:6379
   ```
5. คลิก "Save Changes"

### 5. Redeploy Application
1. ไปที่แท็บ "Deployments"
2. คลิก "Deploy latest commit"
3. รอให้ build เสร็จ

## ข้อมูล Free Tier ของ Upstash:
- **Commands**: 10,000 commands/day
- **Storage**: 256 MB
- **Bandwidth**: 256 MB/day
- **Connections**: 100 concurrent

## ทดสอบการทำงาน:
เมื่อ deploy เสร็จแล้ว ให้ทดสอบโดยเรียก API ของคุณ:
```bash
curl https://your-app.onrender.com/api/your-endpoint
```

ถ้าทำงานเร็วขึ้น แสดงว่า Redis ทำงานแล้ว!

## การ Monitor การใช้งาน:
- ใน Upstash Console จะแสดงสถิติการใช้งาน
- ถ้าใกล้ครบ limit ให้ปรับ cache timeout หรือลด cache key

## Fallback Strategy:
ถ้า Redis ไม่ทำงาน หรือครบ limit แล้ว:
- ระบบจะ fallback เป็น LocMem Cache อัตโนมัติ
- LocMem Cache เร็วกว่า Database Cache แต่จะหายเมื่อ restart

## เปรียบเทียบประสิทธิภาพ:
1. **Redis**: 0.1-1ms (เร็วที่สุด)
2. **LocMem Cache**: 0.01ms (เร็วแต่หายเมื่อ restart)
3. **Database Cache**: 10-100ms (ช้า + ใช้ database quota)
