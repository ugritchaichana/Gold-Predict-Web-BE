#!/bin/bash

echo "🔧 แก้ไขปัญหา PostgreSQL Authentication..."

# หยุด containers
echo "⏹️ หยุด containers..."
docker-compose down

# ลบ volume เก่า (ระวัง: จะลบข้อมูลทั้งหมด!)
echo "🗑️ ลบ PostgreSQL volume เก่า..."
docker volume rm gold-predict-web-be_postgres_data 2>/dev/null || echo "ไม่พบ volume เก่า"

# ตรวจสอบ .env file
echo "📋 ตรวจสอบการตั้งค่าใน .env:"
grep -E "^DB_" .env

echo ""
echo "🔄 เริ่ม PostgreSQL ใหม่..."
docker-compose up -d postgresql

echo "⏳ รอ PostgreSQL เริ่มทำงาน..."
sleep 10

# ตรวจสอบ logs
echo "📝 PostgreSQL logs:"
docker-compose logs postgresql | tail -10

echo ""
echo "🧪 ทดสอบการเชื่อมต่อ:"

# ทดสอบเชื่อมต่อด้วย user ที่สร้าง
echo "1. ทดสอบด้วย goldpredict user:"
docker-compose exec postgresql psql -U goldpredict -d goldpredict_db -c "SELECT version();" 2>&1 && echo "✅ เชื่อมต่อสำเร็จ!" || echo "❌ ยังไม่สามารถเชื่อมต่อได้"

echo ""
echo "2. ทดสอบด้วย postgres user:"
docker-compose exec postgresql psql -U postgres -c "\l" 2>&1 && echo "✅ postgres user ทำงาน" || echo "❌ postgres user มีปัญหา"

echo ""
echo "3. ตรวจสอบ users ที่มี:"
docker-compose exec postgresql psql -U postgres -c "\du" 2>&1 || echo "❌ ไม่สามารถแสดง users ได้"

echo ""
echo "✅ การแก้ไขเสร็จสิ้น!"
echo "💡 หากยังมีปัญหา ลองรัน: ./reset_postgresql.sh"
