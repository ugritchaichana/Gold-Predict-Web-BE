# คู่มือ Deploy Gold Predict Web API บน Render (ทีละขั้นตอน)

## 📖 ขั้นตอนที่ 1: Push โค้ดขึ้น GitHub

### 1.1 สร้าง branch ใหม่และ push
```bash
# เข้าไปใน directory โปรเจ็ค
cd "c:\Users\Ugrit\Desktop\Project\Gold-Predict-Web-BE"

# สร้าง branch ใหม่
git checkout -b render-deployment

# เพิ่มไฟล์ทั้งหมด
git add .

# Commit การเปลี่ยนแปลง
git commit -m "Prepare for Render deployment with Upstash Redis support"

# Push ขึ้น GitHub
git push origin render-deployment
```

## 🌐 ขั้นตอนที่ 2: ตั้งค่า Upstash Redis (ฟรี)

### 2.1 สร้าง Account
1. ไปที่ https://upstash.com/
2. คลิก "Sign Up" และใช้ GitHub account
3. ยืนยัน email

### 2.2 สร้าง Redis Database
1. คลิก "Create Database"
2. Database Name: `gold-predict-cache`
3. Region: **Singapore** (ใกล้ Render Singapore)
4. Type: **Regional** (ฟรี)
5. คลิก "Create"

### 2.3 คัดลอก Connection URL
1. คลิกที่ Database ที่สร้าง
2. ไปที่แท็บ "Details"
3. คัดลอก **Redis URL**
   - ตัวอย่าง: `redis://default:xxxxx@singapore-redis.upstash.io:6379`
4. **เก็บ URL นี้ไว้** จะใช้ในขั้นตอนถัดไป

## 🚀 ขั้นตอนที่ 3: Deploy บน Render

### 3.1 สร้าง Account Render
1. ไปที่ https://dashboard.render.com/
2. คลิก "Get Started" และใช้ GitHub account
3. อนุญาตให้ Render เข้าถึง GitHub

### 3.2 สร้าง Blueprint
1. คลิก "New +"
2. เลือก "Blueprint"
3. เชื่อมต่อ GitHub repository ของคุณ
4. เลือก branch: `render-deployment`
5. Blueprint Name: `gold-predict-web-api`
6. คลิก "Apply"

### 3.3 ตั้งค่า Environment Variables
Render จะสร้าง services อัตโนมัติ แต่ต้องเพิ่ม REDIS_URL:

1. ไปที่ **Web Service** ที่สร้างขึ้น
2. คลิกแท็บ "Environment"
3. เพิ่ม Environment Variable:
   ```
   Key: REDIS_URL
   Value: redis://default:xxxxx@singapore-redis.upstash.io:6379
   ```
   (ใช้ URL ที่คัดลอกจาก Upstash)
4. คลิก "Save Changes"

### 3.4 รอการ Deploy
1. ไปที่แท็บ "Deployments"
2. รอให้ build เสร็จ (5-10 นาทีครั้งแรก)
3. เมื่อสถานะเป็น "Live" แสดงว่าสำเร็จ

## ✅ ขั้นตอนที่ 4: ทดสอบการทำงาน

### 4.1 เข้าถึง Application
1. ใน Render Dashboard คลิกที่ Web Service
2. คัดลอก URL (เช่น https://gold-predict-web-api.onrender.com)
3. เปิดใน browser

### 4.2 ทดสอบ API
```bash
# ทดสอบ API endpoint
curl https://your-app-name.onrender.com/api/your-endpoint

# หรือเปิดใน browser
https://your-app-name.onrender.com/admin/
```

## 🎯 ขั้นตอนที่ 5: Monitor และ Optimize

### 5.1 Monitor Render
- ดูว่า application ทำงานปกติ
- ตรวจสอบ logs ใน "Logs" tab
- ดู resource usage

### 5.2 Monitor Upstash
- เข้า Upstash Console
- ดูการใช้งาน commands/day
- ตรวจสอบไม่เกิน 10,000 commands/day

## 🚨 แก้ไขปัญหาเบื้องต้น

### ถ้า Build ล้มเหลว:
1. ตรวจสอบ logs ใน "Deployments" tab
2. ตรวจสอบ requirements.txt ว่าไม่มี syntax error
3. ตรวจสอบ Python version compatibility

### ถ้า Application ไม่ทำงาน:
1. ตรวจสอบ Environment Variables
2. ตรวจสอบ REDIS_URL ถูกต้อง
3. ดู error logs ใน "Logs" tab

### ถ้า Cache ไม่ทำงาน:
1. ตรวจสอบ REDIS_URL ใน Environment Variables
2. ตรวจสอบ Upstash Redis ยังทำงาน
3. Redis จะ fallback เป็น LocMem Cache อัตโนมัติ

## 🎉 เสร็จสิ้น!
ถ้าทุกอย่างทำงานดี คุณจะมี:
- ✅ Django API ทำงานบน Render
- ✅ PostgreSQL Database (ฟรี)
- ✅ Redis Cache ผ่าน Upstash (ฟรี)
- ✅ Static files ทำงานด้วย WhiteNoise
- ✅ HTTPS อัตโนมัติ

**URL สุดท้าย**: `https://your-app-name.onrender.com`
