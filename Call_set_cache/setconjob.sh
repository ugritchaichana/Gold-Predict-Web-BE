#!/bin/bash

# กำหนด path
PYTHON_PATH=$(command -v python3)
SCRIPT_PATH="/home/toonasboothas/Gold-Predict-Web-BE/Call_set_cache/call_api.py"
LOG_PATH="/home/toonasboothas/Gold-Predict-Web-BE/Call_set_cache/log.txt"

# cron job ที่จะเพิ่ม
CRON_JOB="*/7 * * * * $PYTHON_PATH $SCRIPT_PATH >> $LOG_PATH 2>&1"

# ตรวจสอบว่ามี cron นี้อยู่แล้วหรือยัง (match ทั้งบรรทัด)
(crontab -l 2>/dev/null | grep -Fx "$CRON_JOB") > /dev/null

if [ $? -eq 0 ]; then
    echo "✅ Cron job already exists."
else
    # เพิ่ม cron job
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "✅ Cron job added: $CRON_JOB"
fi
