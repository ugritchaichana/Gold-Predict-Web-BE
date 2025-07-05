#!/bin/bash

# สคริปต์ตั้งค่า Docker Daemon สำหรับจัดการ logs

echo "🔧 กำลังตั้งค่า Docker Daemon..."

# สำรองไฟล์ daemon.json เดิม (ถ้ามี)
if [ -f /etc/docker/daemon.json ]; then
    sudo cp /etc/docker/daemon.json /etc/docker/daemon.json.backup.$(date +%Y%m%d_%H%M%S)
    echo "✅ สำรองไฟล์ daemon.json เดิมแล้ว"
fi

# สร้าง directory ถ้าไม่มี
sudo mkdir -p /etc/docker

# คัดลอกไฟล์ daemon.json
sudo cp daemon.json /etc/docker/daemon.json

# ตั้งค่าสิทธิ์
sudo chmod 644 /etc/docker/daemon.json

# รีสตาร์ท Docker service
echo "🔄 กำลังรีสตาร์ท Docker service..."
sudo systemctl daemon-reload
sudo systemctl restart docker

# ตรวจสอบสถานะ
if sudo systemctl is-active --quiet docker; then
    echo "✅ Docker service ทำงานปกติ"
else
    echo "❌ เกิดข้อผิดพลาดกับ Docker service"
    sudo systemctl status docker
    exit 1
fi

# แสดงข้อมูล Docker
echo ""
echo "📊 ข้อมูล Docker:"
docker info | grep -E "(Logging Driver|Storage Driver)"

echo ""
echo "✅ ตั้งค่า Docker Daemon เสร็จสิ้น!"
