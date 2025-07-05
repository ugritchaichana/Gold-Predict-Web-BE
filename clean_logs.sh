#!/bin/bash

# สคริปต์สำหรับทำความสะอาด log files เก่า
# ใช้งาน: ./clean_logs.sh [days] 
# หากไม่ระบุ days จะใช้ค่าเริ่มต้น 30 วัน

DAYS=${1:-30}  # ค่าเริ่มต้น 30 วัน หากไม่ได้ระบุ
LOG_DIR="./logs"

echo "กำลังลบ log files ที่เก่ากว่า $DAYS วัน..."

# ลบ log files เก่า
find "$LOG_DIR" -type f -name "*.log*" -mtime +$DAYS -exec rm -f {} \;

# ลบ Docker logs เก่า (ต้องมี sudo)
echo "กำลังลบ Docker logs เก่า..."
sudo docker system prune -f --filter "until=${DAYS}h"

# แสดงขนาดของ logs directory ปัจจุบัน
echo "ขนาดของ logs directory ปัจจุบัน:"
du -sh "$LOG_DIR" 2>/dev/null || echo "ไม่พบ logs directory"

echo "การทำความสะอาดเสร็จสิ้น!"
