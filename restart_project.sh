#!/bin/bash

echo "🔄 รีสตาร์ทโปรเจ็ค Gold Predict Web..."

# หยุด containers ทั้งหมด
echo "⏹️ หยุด containers..."
docker-compose down

# สร้างและเริ่ม containers ใหม่
echo "🚀 เริ่ม containers ใหม่..."
docker-compose up -d --build

# รอระบบเริ่มทำงาน
echo "⏳ รอระบบเริ่มทำงาน..."
sleep 20

# ตรวจสอบสถานะ
echo "📊 ตรวจสอบสถานะ containers:"
docker-compose ps

echo ""
echo "🧪 ทดสอบ endpoints:"
echo "1. Health Check:"
curl -s http://localhost:8000/health/ && echo " ✅" || echo " ❌"

echo "2. ตรวจสอบ services อื่นๆ:"
echo "   - Currency: http://localhost:8000/currency/"
echo "   - Gold: http://localhost:8000/gold/"
echo "   - Predicts: http://localhost:8000/predicts/"
echo "   - Data: http://localhost:8000/data/"

echo ""
echo "📝 ดู logs (กด Ctrl+C เพื่อหยุด):"
echo "docker-compose logs -f"

echo ""
echo "✅ รีสตาร์ทเสร็จสิ้น!"
