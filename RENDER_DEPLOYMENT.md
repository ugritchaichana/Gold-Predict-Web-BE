# การ Deploy โปรเจ็ค Gold Predict Web API บน Render

## ขั้นตอนการ Deploy บน Render (Free Tier)

### 1. เตรียมโปรเจ็ค
- ใส่โค้ดลงใน GitHub repository
- ตรวจสอบว่าไฟล์ `render.yaml` อยู่ใน root directory

### 2. สร้าง Service บน Render
1. ไปที่ [Render Dashboard](https://dashboard.render.com/)
2. เลือก "New" → "Blueprint"
3. เชื่อมต่อ GitHub repository
4. Render จะอ่านการตั้งค่าจากไฟล์ `render.yaml` อัตโนมัติ

### 3. ตั้งค่า Environment Variables
ใน Render Dashboard ให้เพิ่ม Environment Variables ต่อไปนี้:

```
RENDER=true
DEBUG=false
SECRET_KEY=your-super-secret-key-here
ALLOWED_HOSTS=*
```

**หมายเหตุ:** `DATABASE_URL` และ `REDIS_URL` จะถูกสร้างอัตโนมัติโดย Render

### 4. ข้อจำกัดของ Render Free Tier
- **Database**: PostgreSQL 1GB storage, 97 hours uptime per month
- **Redis**: ❌ ไม่รองรับ Redis service (ใช้ Database Cache แทน)
- **Web Service**: 750 hours per month, sleep หลัง 15 นาทีไม่มีการใช้งาน
- **Build time**: จำกัดเวลา build

**สำคัญ**: โปรเจ็คนี้ใช้ Database Cache แทน Redis เพื่อให้เข้ากันได้กับ Render Free Tier

### 5. การใช้งาน Docker Compose (Local Development)
```bash
# คัดลอกไฟล์ตัวอย่าง environment variables
cp .env.example .env

# แก้ไขไฟล์ .env ตามการตั้งค่าของคุณ
# จากนั้นรัน docker compose
docker-compose up --build
```

### 6. ปัญหาที่อาจพบและการแก้ไข

#### ปัญหา: Static Files ไม่โหลด
- ตรวจสอบว่าได้เพิ่ม `whitenoise` ใน middleware แล้ว
- รัน `python manage.py collectstatic` ใน build command

#### ปัญหา: Database Connection Error
- ตรวจสอบการตั้งค่า `DATABASE_URL` ใน Environment Variables
- ใช้ `dj_database_url.parse()` เพื่อแปลง URL เป็น Django database config

#### ปัญหา: Redis Connection Error
- ❌ **ไม่ใช้ Redis บน Render Free Tier**
- ✅ **ใช้ Database Cache แทน** (ตั้งค่าอัตโนมัติใน settings.py)
- Cache table จะถูกสร้างอัตโนมัติใน build process

### 7. การ Monitor และ Debug
- ใช้ Render Logs เพื่อดู application logs
- ตรวจสอบ Health Check ใน Render Dashboard
- ใช้ `DEBUG=true` เฉพาะเวลา debug (อย่าใช้ใน production)

### 8. การปรับปรุงประสิทธิภาพ
- ใช้ Redis caching เพื่อลด database queries
- ตั้งค่า `ALLOWED_HOSTS` เฉพาะ domain ที่จำเป็น
- เพิ่ม database indexing สำหรับ queries ที่ใช้บ่อย

## ไฟล์ที่สำคัญสำหรับ Render
- `render.yaml`: การตั้งค่า services และ infrastructure
- `requirements.txt`: Python dependencies
- `Backend/settings.py`: การตั้งค่า Django สำหรับ production
- `.env.example`: ตัวอย่างการตั้งค่า environment variables
