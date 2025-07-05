#!/bin/bash

echo "🔍 ตรวจสอบสถานะ PostgreSQL Container..."

# ตรวจสอบ containers ที่ทำงาน
echo "📋 Docker Containers:"
docker-compose ps

echo ""
echo "🔍 ตรวจสอบ PostgreSQL logs:"
docker-compose logs postgresql | tail -20

echo ""
echo "🔍 ตรวจสอบ environment variables ใน container:"
docker-compose exec postgresql env | grep POSTGRES

echo ""
echo "🔍 ลองเชื่อมต่อจากภายใน container:"
docker-compose exec postgresql psql -U goldpredict -d goldpredict_db -c "\l" 2>&1 || echo "❌ ไม่สามารถเชื่อมต่อได้"

echo ""
echo "🔍 ตรวจสอบ users ใน PostgreSQL:"
docker-compose exec postgresql psql -U postgres -c "\du" 2>&1 || echo "❌ ไม่สามารถดู users ได้"
