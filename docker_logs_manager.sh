#!/bin/bash

# สคริปต์สำหรับจัดการ Docker Logs อย่างมีประสิทธิภาพ
# รองรับ Docker Engine 26.1.4 และ Docker Compose v2.27.1

# ฟังก์ชันแสดงขนาด logs
show_log_sizes() {
    echo "📊 ขนาด Docker Logs ปัจจุบัน:"
    echo "================================="
    
    # แสดงขนาด container logs
    echo "🐳 Container Logs:"
    sudo du -sh /var/lib/docker/containers/*/
    echo ""
    
    # แสดงขนาด application logs
    echo "📝 Application Logs:"
    du -sh ./logs/ 2>/dev/null || echo "ไม่พบ logs directory"
    echo ""
    
    # แสดงรวม Docker system
    echo "💾 Docker System Usage:"
    sudo docker system df
}

# ฟังก์ชันดู logs แบบ real-time
view_logs() {
    local service=$1
    if [ -z "$service" ]; then
        echo "📋 Services ที่มี:"
        docker-compose ps --services
        echo ""
        echo "💡 ใช้งาน: $0 logs <service_name>"
        echo "ตัวอย่าง: $0 logs app"
        return 1
    fi
    
    echo "👀 กำลังดู logs ของ $service (กด Ctrl+C เพื่อหยุด):"
    docker-compose logs -f --tail=100 "$service"
}

# ฟังก์ชันทำความสะอาด logs
clean_logs() {
    local days=${1:-7}
    
    echo "🧹 กำลังทำความสะอาด logs เก่ากว่า $days วัน..."
    
    # ทำความสะอาด application logs
    echo "📝 ทำความสะอาด application logs..."
    find ./logs -type f -name "*.log*" -mtime +$days -exec rm -f {} \; 2>/dev/null
    
    # ทำความสะอาด Docker logs
    echo "🐳 ทำความสะอาด Docker system..."
    sudo docker system prune -f --filter "until=${days}h"
    
    # ทำความสะอาด unused images
    echo "🖼️ ลบ images ที่ไม่ใช้..."
    sudo docker image prune -f
    
    # ทำความสะอาด volumes ที่ไม่ใช้ (ระวัง!)
    echo "💾 ลบ volumes ที่ไม่ใช้..."
    sudo docker volume prune -f
    
    echo "✅ ทำความสะอาดเสร็จสิ้น!"
    echo ""
    show_log_sizes
}

# ฟังก์ชันสำรอง logs
backup_logs() {
    local backup_dir="./logs_backup/$(date +%Y%m%d_%H%M%S)"
    
    echo "💾 กำลังสำรอง logs..."
    mkdir -p "$backup_dir"
    
    # สำรอง application logs
    if [ -d "./logs" ]; then
        cp -r ./logs/* "$backup_dir/" 2>/dev/null
        echo "✅ สำรอง application logs เสร็จสิ้น"
    fi
    
    # สำรอง container logs (เฉพาะที่สำคัญ)
    echo "🐳 สำรอง container logs..."
    for container in $(docker-compose ps -q); do
        container_name=$(docker inspect --format='{{.Name}}' $container | sed 's/^\/*//')
        docker logs $container > "$backup_dir/${container_name}.log" 2>&1
    done
    
    # บีบอัด backup
    cd ./logs_backup
    tar -czf "$(basename $backup_dir).tar.gz" "$(basename $backup_dir)"
    rm -rf "$(basename $backup_dir)"
    cd - > /dev/null
    
    echo "✅ สำรอง logs เสร็จสิ้น: ./logs_backup/$(basename $backup_dir).tar.gz"
}

# ฟังก์ชันแสดงสถิติ logs
log_stats() {
    echo "📈 สถิติ Docker Logs:"
    echo "===================="
    
    # นับจำนวน log entries ใน containers
    echo "📊 จำนวน log entries ใน containers:"
    for container in $(docker-compose ps -q); do
        container_name=$(docker inspect --format='{{.Name}}' $container | sed 's/^\/*//')
        log_count=$(docker logs $container 2>&1 | wc -l)
        echo "  $container_name: $log_count lines"
    done
    echo ""
    
    # แสดง log levels ใน application logs
    if [ -d "./logs" ]; then
        echo "📋 Log levels ใน application logs:"
        for log_file in ./logs/*.log; do
            if [ -f "$log_file" ]; then
                echo "  $(basename $log_file):"
                grep -o '\(DEBUG\|INFO\|WARNING\|ERROR\|CRITICAL\)' "$log_file" 2>/dev/null | sort | uniq -c | sort -nr || echo "    ไม่พบ log levels"
            fi
        done
    fi
}

# Main script
case "$1" in
    "size"|"sizes")
        show_log_sizes
        ;;
    "logs"|"view")
        view_logs "$2"
        ;;
    "clean")
        clean_logs "$2"
        ;;
    "backup")
        backup_logs
        ;;
    "stats")
        log_stats
        ;;
    *)
        echo "🔧 Docker Logs Management Tool"
        echo "=============================="
        echo ""
        echo "📋 คำสั่งที่ใช้ได้:"
        echo "  $0 size              - แสดงขนาด logs"
        echo "  $0 logs [service]    - ดู logs แบบ real-time"
        echo "  $0 clean [days]      - ทำความสะอาด logs (default: 7 วัน)"
        echo "  $0 backup            - สำรอง logs"
        echo "  $0 stats             - แสดงสถิติ logs"
        echo ""
        echo "💡 ตัวอย่าง:"
        echo "  $0 logs app          - ดู logs ของ app service"
        echo "  $0 clean 30          - ลบ logs เก่ากว่า 30 วัน"
        ;;
esac
