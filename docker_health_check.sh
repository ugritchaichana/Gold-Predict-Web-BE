#!/bin/bash

# สคริปต์เช็คสุขภาพระบบ Docker
# รองรับ Docker Engine 26.1.4 และ Docker Compose v2.27.1

echo "🏥 เช็คสุขภาพระบบ Docker"
echo "========================="

# เช็ค Docker versions
echo "📋 เช็ค Docker Versions:"
echo "  Docker Engine: $(docker --version | awk '{print $3}' | sed 's/,//')"
echo "  Docker Compose: $(docker-compose --version | awk '{print $4}' | sed 's/,//')"
echo "  Containerd: $(containerd --version | awk '{print $3}')"
echo ""

# เช็ค Docker daemon
echo "🔧 เช็ค Docker Daemon:"
if sudo systemctl is-active --quiet docker; then
    echo "  ✅ Docker daemon ทำงานปกติ"
else
    echo "  ❌ Docker daemon ไม่ทำงาน"
    echo "  💡 ลองรัน: sudo systemctl start docker"
fi
echo ""

# เช็ค Docker containers
echo "🐳 เช็ค Docker Containers:"
docker-compose ps
echo ""

# เช็ค health checks
echo "❤️ เช็ค Container Health:"
for container in $(docker-compose ps -q); do
    container_name=$(docker inspect --format='{{.Name}}' $container | sed 's/^\/*//')
    health_status=$(docker inspect --format='{{.State.Health.Status}}' $container 2>/dev/null)
    
    if [ "$health_status" = "healthy" ]; then
        echo "  ✅ $container_name: Healthy"
    elif [ "$health_status" = "unhealthy" ]; then
        echo "  ❌ $container_name: Unhealthy"
    elif [ "$health_status" = "starting" ]; then
        echo "  🟡 $container_name: Starting"
    else
        echo "  ⚪ $container_name: No health check"
    fi
done
echo ""

# เช็ค resource usage
echo "💾 เช็ค Resource Usage:"
echo "  Memory Usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
echo ""

# เช็ค disk usage
echo "💿 เช็ค Disk Usage:"
sudo docker system df
echo ""

# เช็ค logs sizes
echo "📊 เช็ค Logs Sizes:"
echo "  Application logs:"
du -sh ./logs/ 2>/dev/null || echo "    ไม่พบ logs directory"

echo "  Container logs:"
total_size=$(sudo du -sh /var/lib/docker/containers/ 2>/dev/null | awk '{print $1}')
echo "    Total: $total_size"
echo ""

# เช็ค network connectivity
echo "🌐 เช็ค Network Connectivity:"
if docker network ls | grep -q "gold-predict-web-be_default"; then
    echo "  ✅ Docker network ทำงานปกติ"
else
    echo "  ⚠️ ไม่พบ Docker network"
fi

# เช็ค port availability
echo "  Port availability:"
for port in 8000 5432 6379; do
    if ss -tuln | grep ":$port " > /dev/null; then
        echo "    ✅ Port $port: ใช้งานอยู่"
    else
        echo "    ⚪ Port $port: ว่าง"
    fi
done
echo ""

# เช็ค log rotation
echo "🔄 เช็ค Log Rotation Settings:"
if [ -f /etc/docker/daemon.json ]; then
    if grep -q "log-opts" /etc/docker/daemon.json; then
        echo "  ✅ Log rotation ตั้งค่าแล้ว"
        max_size=$(sudo grep -A 5 "log-opts" /etc/docker/daemon.json | grep "max-size" | awk -F'"' '{print $4}')
        max_file=$(sudo grep -A 5 "log-opts" /etc/docker/daemon.json | grep "max-file" | awk -F'"' '{print $4}')
        echo "    Max size: $max_size, Max files: $max_file"
    else
        echo "  ⚠️ Log rotation ยังไม่ตั้งค่า"
    fi
else
    echo "  ⚠️ ไม่พบไฟล์ daemon.json"
fi
echo ""

# เช็ค recent errors
echo "❗ เช็ค Recent Errors (24 ชั่วโมงที่ผ่านมา):"
error_count=0
for container in $(docker-compose ps -q); do
    container_name=$(docker inspect --format='{{.Name}}' $container | sed 's/^\/*//')
    errors=$(docker logs --since="24h" $container 2>&1 | grep -i "error\|exception\|fatal" | wc -l)
    if [ $errors -gt 0 ]; then
        echo "  ⚠️ $container_name: $errors errors"
        error_count=$((error_count + errors))
    fi
done

if [ $error_count -eq 0 ]; then
    echo "  ✅ ไม่พบ errors ในระบบ"
else
    echo "  ⚠️ รวม: $error_count errors"
fi
echo ""

# สรุป
echo "📝 สรุป:"
echo "======="
if sudo systemctl is-active --quiet docker && [ $error_count -eq 0 ]; then
    echo "✅ ระบบทำงานปกติ สุขภาพดี!"
else
    echo "⚠️ ระบบมีปัญหาบางอย่าง ควรตรวจสอบ"
fi
