#!/bin/bash

# สคริปต์แก้ไขปัญหา Docker Daemon
echo "🔧 แก้ไขปัญหา Docker Daemon..."

# หยุด Docker service
echo "⏹️ หยุด Docker service..."
sudo systemctl stop docker
sudo systemctl stop docker.socket

# สำรองไฟล์ daemon.json เดิม (ถ้ามี)
if [ -f /etc/docker/daemon.json ]; then
    echo "💾 สำรองไฟล์ daemon.json เดิม..."
    sudo cp /etc/docker/daemon.json /etc/docker/daemon.json.backup.$(date +%Y%m%d_%H%M%S)
fi

# ลบไฟล์ daemon.json ที่มีปัญหา
echo "🗑️ ลบไฟล์ daemon.json ที่มีปัญหา..."
sudo rm -f /etc/docker/daemon.json

# เริ่ม Docker ใหม่แบบ default configuration
echo "🔄 เริ่ม Docker ด้วย default configuration..."
sudo systemctl daemon-reload
sudo systemctl start docker

# ตรวจสอบสถานะ
if sudo systemctl is-active --quiet docker; then
    echo "✅ Docker เริ่มทำงานปกติแล้ว!"
    
    # ใช้ daemon.json ใหม่ที่แก้ไขแล้ว
    echo "📝 ใช้ daemon.json ใหม่..."
    sudo mkdir -p /etc/docker
    sudo cp daemon.json /etc/docker/daemon.json
    sudo chmod 644 /etc/docker/daemon.json
    
    # รีสตาร์ท Docker อีกครั้ง
    echo "🔄 รีสตาร์ท Docker ด้วยการตั้งค่าใหม่..."
    sudo systemctl daemon-reload
    sudo systemctl restart docker
    
    # ตรวจสอบอีกครั้ง
    if sudo systemctl is-active --quiet docker; then
        echo "✅ Docker ทำงานปกติด้วยการตั้งค่าใหม่!"
        docker --version
        echo ""
        echo "📊 ตรวจสอบการตั้งค่า logging:"
        docker info | grep -E "(Logging Driver|Storage Driver)" || true
    else
        echo "❌ ยังมีปัญหา กำลังกลับไปใช้ default configuration..."
        sudo rm -f /etc/docker/daemon.json
        sudo systemctl daemon-reload
        sudo systemctl restart docker
        
        if sudo systemctl is-active --quiet docker; then
            echo "✅ Docker ทำงานด้วย default configuration"
            echo "⚠️ ไม่ได้ใช้การตั้งค่า log rotation"
        else
            echo "❌ Docker ยังไม่ทำงาน ต้องตรวจสอบเพิ่มเติม"
            echo "🔍 ดู logs เพิ่มเติม:"
            sudo journalctl -xeu docker.service --no-pager -l
        fi
    fi
else
    echo "❌ Docker ยังไม่ทำงาน ลองทำต่อ..."
    
    # ลบไฟล์ที่อาจจะมีปัญหา
    echo "🧹 ทำความสะอาดไฟล์ Docker..."
    sudo rm -rf /var/lib/docker/network/files
    sudo rm -rf /var/lib/docker/swarm
    
    # รีสตาร์ท containerd
    echo "🔄 รีสตาร์ท containerd..."
    sudo systemctl restart containerd
    sleep 2
    
    # เริ่ม Docker อีกครั้ง
    echo "🔄 เริ่ม Docker อีกครั้ง..."
    sudo systemctl start docker
    
    if sudo systemctl is-active --quiet docker; then
        echo "✅ Docker ทำงานแล้ว!"
    else
        echo "❌ ยังมีปัญหา แสดง logs:"
        sudo journalctl -xeu docker.service --no-pager -l | tail -20
    fi
fi

echo ""
echo "🏁 สรุป:"
if sudo systemctl is-active --quiet docker; then
    echo "✅ Docker ทำงานปกติ"
    echo "💡 ลองรัน: docker run hello-world"
else
    echo "❌ Docker ยังมีปัญหา"
    echo "💡 ลองรัน: sudo journalctl -xeu docker.service"
fi
