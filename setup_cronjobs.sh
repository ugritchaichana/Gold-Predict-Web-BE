#!/bin/bash

# Script สำหรับตั้งค่า Cron Jobs บน Ubuntu Server
# สำหรับ Gold Predict Web Backend

echo "Setting up Cron Jobs for Gold Predict Web Backend..."

# สร้าง script สำหรับ fetch gold data และ currency data
cat > ~/fetch_all_data.sh << 'EOF'
#!/bin/bash
# Script สำหรับดึงข้อมูลราคาทองคำและอัตราแลกเปลี่ยน
LOG_FILE=~/logs/fetch_all_data.log
mkdir -p ~/logs

echo "$(date): Starting data fetch (gold + currency)..." >> $LOG_FILE

# ดึงข้อมูลทองคำจาก db_choice=0
echo "$(date): Fetching gold data for db_choice=0..." >> $LOG_FILE
curl -s "http://localhost:8000/finnomenaGold/fetch-gold-data/?db_choice=0" >> $LOG_FILE 2>&1
if [ $? -eq 0 ]; then
    echo "$(date): Successfully fetched gold data for db_choice=0" >> $LOG_FILE
else
    echo "$(date): Failed to fetch gold data for db_choice=0" >> $LOG_FILE
fi

# ดึงข้อมูลทองคำจาก db_choice=1
echo "$(date): Fetching gold data for db_choice=1..." >> $LOG_FILE
curl -s "http://localhost:8000/finnomenaGold/fetch-gold-data/?db_choice=1" >> $LOG_FILE 2>&1
if [ $? -eq 0 ]; then
    echo "$(date): Successfully fetched gold data for db_choice=1" >> $LOG_FILE
else
    echo "$(date): Failed to fetch gold data for db_choice=1" >> $LOG_FILE
fi

# ดึงข้อมูลอัตราแลกเปลี่ยน USD/THB
echo "$(date): Fetching USD/THB exchange rate..." >> $LOG_FILE
curl -s "http://localhost:8000/currency/update-daily-usdthb/?update_existing=true" >> $LOG_FILE 2>&1
if [ $? -eq 0 ]; then
    echo "$(date): Successfully fetched USD/THB exchange rate" >> $LOG_FILE
else
    echo "$(date): Failed to fetch USD/THB exchange rate" >> $LOG_FILE
fi

echo "$(date): All data fetch completed" >> $LOG_FILE
echo "========================================" >> $LOG_FILE
EOF

# ทำให้ script สามารถรันได้
chmod +x ~/fetch_all_data.sh

# สร้าง script สำหรับ DuckDNS
cat > ~/duckdns_update.sh << 'EOF'
#!/bin/bash
# Script สำหรับต่ออายุ DuckDNS
# กรุณาแก้ไข YOUR_DOMAIN และ YOUR_TOKEN ให้เป็นค่าจริงของคุณ

DOMAIN="YOUR_DOMAIN"  # เปลี่ยนเป็นโดเมน DuckDNS ของคุณ
TOKEN="YOUR_TOKEN"    # เปลี่ยนเป็น Token ของคุณ
LOG_FILE=~/logs/duckdns.log

mkdir -p ~/logs

echo "$(date): Updating DuckDNS for domain: $DOMAIN" >> $LOG_FILE

# อัพเดท DuckDNS
RESPONSE=$(curl -s "https://www.duckdns.org/update?domains=$DOMAIN&token=$TOKEN&ip=")

if [ "$RESPONSE" = "OK" ]; then
    echo "$(date): DuckDNS update successful" >> $LOG_FILE
else
    echo "$(date): DuckDNS update failed. Response: $RESPONSE" >> $LOG_FILE
fi

echo "----------------------------------------" >> $LOG_FILE
EOF

# ทำให้ script สามารถรันได้
chmod +x ~/duckdns_update.sh

# สร้างไฟล์ crontab
cat > ~/temp_crontab << 'EOF'
# Cron Jobs สำหรับ Gold Predict Web Backend

# ดึงข้อมูลราคาทองคำและอัตราแลกเปลี่ยนทุกๆ 4 ชั่วโมง (เวลา 0 นาที ของชั่วโมงที่ 0, 4, 8, 12, 16, 20)
0 */4 * * * ~/fetch_all_data.sh

# อัพเดท DuckDNS ทุกๆ 5 นาที
*/5 * * * * ~/duckdns_update.sh
EOF

# ติดตั้ง crontab
crontab ~/temp_crontab

# ลบไฟล์ temp
rm ~/temp_crontab

echo "Cron Jobs ได้ถูกตั้งค่าเรียบร้อยแล้ว!"
echo ""
echo "รายการ Cron Jobs ที่ติดตั้ง:"
crontab -l
echo ""
echo "คำแนะนำ:"
echo "1. แก้ไขไฟล์ ~/duckdns_update.sh เพื่อใส่ DOMAIN และ TOKEN ของคุณ"
echo "2. ตรวจสอบ log files ที่ ~/logs/"
echo "3. ทดสอบ scripts โดยรันคำสั่ง:"
echo "   ~/fetch_all_data.sh"
echo "   ~/duckdns_update.sh"
echo ""
echo "การทำงานของ Cron Jobs:"
echo "- ดึงข้อมูลทองคำและอัตราแลกเปลี่ยน: ทุกๆ 4 ชั่วโมง (00:00, 04:00, 08:00, 12:00, 16:00, 20:00)"
echo "- อัพเดท DuckDNS: ทุกๆ 5 นาที"
