#!/bin/bash

echo "🔄 รีเซ็ต PostgreSQL ทั้งหมด..."
echo "⚠️ ข้อมูลทั้งหมดจะถูกลบ!"

read -p "ยืนยันการรีเซ็ต? (y/N): " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo "❌ ยกเลิกการรีเซ็ต"
    exit 1
fi

# หยุดทุก containers
echo "⏹️ หยุด containers ทั้งหมด..."
docker-compose down

# ลบ volumes ทั้งหมด
echo "🗑️ ลบ volumes..."
docker volume rm gold-predict-web-be_postgres_data 2>/dev/null || echo "ไม่พบ postgres volume"
docker volume rm gold-predict-web-be_redis_data 2>/dev/null || echo "ไม่พบ redis volume"

# ลบ containers และ images ที่ไม่ใช้
echo "🧹 ทำความสะอาด Docker..."
docker container prune -f
docker image prune -f

# สร้าง containers ใหม่
echo "🔨 สร้าง containers ใหม่..."
docker-compose up -d --build

echo "⏳ รอระบบเริ่มทำงาน..."
sleep 15

# ตรวจสอบสถานะ
echo "📊 ตรวจสอบสถานะ:"
docker-compose ps

echo ""
echo "🧪 ทดสอบการเชื่อมต่อ PostgreSQL:"
docker-compose exec postgresql psql -U goldpredict -d goldpredict_db -c "SELECT 'Connection successful!' as status;" 2>&1 && echo "✅ PostgreSQL พร้อมใช้งาน!" || echo "❌ ยังมีปัญหา"

echo ""
echo "🧪 ทดสอบการเชื่อมต่อ Redis:"
docker-compose exec redis redis-cli ping 2>&1 && echo "✅ Redis พร้อมใช้งาน!" || echo "❌ Redis มีปัญหา"

echo ""
echo "📝 ข้อมูลการเชื่อมต่อ:"
echo "========================="
echo "Database: goldpredict_db"
echo "Username: goldpredict"
echo "Password: goldpredict"
echo "Host: localhost (ผ่าน SSH tunnel) หรือ 3.1.201.90 (direct)"
echo "Port: 5432"

echo ""
echo "✅ รีเซ็ตเสร็จสิ้น!"
