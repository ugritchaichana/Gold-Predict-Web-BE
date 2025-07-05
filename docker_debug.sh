#!/bin/bash

# สคริปต์ตรวจสอบ Docker แบบละเอียด
echo "🔍 ตรวจสอบสถานะ Docker แบบละเอียด"
echo "====================================="

# ตรวจสอบ Docker service
echo "1. 🐳 Docker Service Status:"
sudo systemctl status docker.service --no-pager -l || echo "❌ Docker service มีปัญหา"
echo ""

# ตรวจสอบ containerd
echo "2. 📦 Containerd Status:"
sudo systemctl status containerd.service --no-pager -l || echo "❌ Containerd มีปัญหา"
echo ""

# ตรวจสอบ Docker socket
echo "3. 🔌 Docker Socket:"
sudo systemctl status docker.socket --no-pager -l || echo "❌ Docker socket มีปัญหา"
echo ""

# ตรวจสอบไฟล์ daemon.json
echo "4. ⚙️ Docker Daemon Configuration:"
if [ -f /etc/docker/daemon.json ]; then
    echo "✅ พบไฟล์ /etc/docker/daemon.json"
    echo "📄 เนื้อหา:"
    sudo cat /etc/docker/daemon.json | jq . 2>/dev/null || {
        echo "❌ JSON ไม่ถูกต้อง:"
        sudo cat /etc/docker/daemon.json
    }
else
    echo "⚪ ไม่พบไฟล์ daemon.json (ใช้ default settings)"
fi
echo ""

# ตรวจสอบ Docker logs
echo "5. 📝 Docker Service Logs (ล่าสุด):"
sudo journalctl -u docker.service --no-pager -l -n 10 || echo "❌ ไม่สามารถดู logs ได้"
echo ""

# ตรวจสอบ process
echo "6. 🔄 Docker Processes:"
ps aux | grep docker | grep -v grep || echo "❌ ไม่พบ Docker processes"
echo ""

# ตรวจสอบ storage driver
echo "7. 💾 Storage Information:"
if sudo systemctl is-active --quiet docker; then
    docker info | grep -E "(Storage Driver|Backing Filesystem|Data Space)" 2>/dev/null || echo "❌ ไม่สามารถดูข้อมูล storage ได้"
else
    echo "❌ Docker ไม่ทำงาน ไม่สามารถดูข้อมูล storage ได้"
fi
echo ""

# ตรวจสอบ network
echo "8. 🌐 Network Information:"
ip link show docker0 2>/dev/null && echo "✅ Docker bridge network ทำงานปกติ" || echo "❌ ไม่พบ Docker bridge network"
echo ""

# ตรวจสอบ disk space
echo "9. 💿 Disk Space:"
df -h /var/lib/docker 2>/dev/null || df -h /
echo ""

# ตรวจสอบ permissions
echo "10. 🔐 Permissions:"
ls -la /var/run/docker.sock 2>/dev/null || echo "❌ ไม่พบ Docker socket"
echo ""

# สรุป
echo "📋 สรุปผลการตรวจสอบ:"
echo "========================"

if sudo systemctl is-active --quiet docker; then
    echo "✅ Docker: ทำงานปกติ"
else
    echo "❌ Docker: ไม่ทำงาน"
fi

if sudo systemctl is-active --quiet containerd; then
    echo "✅ Containerd: ทำงานปกติ"
else
    echo "❌ Containerd: ไม่ทำงาน"
fi

if [ -f /etc/docker/daemon.json ]; then
    if sudo cat /etc/docker/daemon.json | jq . >/dev/null 2>&1; then
        echo "✅ daemon.json: ไวยากรณ์ถูกต้อง"
    else
        echo "❌ daemon.json: ไวยากรณ์ผิด"
    fi
else
    echo "⚪ daemon.json: ไม่มีไฟล์ (ใช้ค่า default)"
fi

echo ""
echo "💡 คำแนะนำ:"
if ! sudo systemctl is-active --quiet docker; then
    echo "  - รัน: chmod +x fix_docker.sh && ./fix_docker.sh"
else
    echo "  - Docker ทำงานปกติแล้ว!"
fi
