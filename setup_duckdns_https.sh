#!/bin/bash

# สคริปต์ตั้งค่า Duck DNS + Let's Encrypt ดึงข้อมูลจาก .env
# ใช้งาน: ./setup_duckdns_https.sh

APP_DIR=$(pwd)

# อ่านข้อมูลจากไฟล์ .env
if [ -f "${APP_DIR}/.env" ]; then
    echo "กำลังอ่านข้อมูลจากไฟล์ .env..."
    export $(grep -v '^#' ${APP_DIR}/.env | xargs)
else
    echo "ไม่พบไฟล์ .env กรุณาตรวจสอบ"
    exit 1
fi

# ตรวจสอบว่ามีข้อมูล Duck DNS หรือไม่
if [ -z "$DUCK_DNS_TOKEN" ] || [ -z "$DUCK_DNS_DOMAIN" ]; then
    echo "ไม่พบข้อมูล DUCK_DNS_TOKEN หรือ DUCK_DNS_DOMAIN ในไฟล์ .env"
    exit 1
fi

# แยกชื่อโดเมนย่อยจากโดเมนเต็ม (เช่น goldpredictions จาก goldpredictions.duckdns.org)
SUBDOMAIN=$(echo $DUCK_DNS_DOMAIN | cut -d. -f1)
DOMAIN=$DUCK_DNS_DOMAIN
TOKEN=$DUCK_DNS_TOKEN

echo "ข้อมูล Duck DNS:"
echo "- โดเมน: $DOMAIN"
echo "- โดเมนย่อย: $SUBDOMAIN"
echo "- โทเค็น: $TOKEN"

# อัปเดตระบบ
echo "กำลังอัปเดตระบบ..."
sudo apt update
sudo apt upgrade -y

# ติดตั้ง Nginx และ Certbot
echo "กำลังติดตั้ง Nginx, Certbot และเครื่องมือที่จำเป็น..."
sudo apt install nginx certbot python3-certbot-nginx python3-pip cron curl -y

# ตั้งค่า Duck DNS auto-update
echo "กำลังตั้งค่า Duck DNS..."
mkdir -p ~/duckdns
cat > ~/duckdns/duck.sh << EOF
#!/bin/bash
echo url="https://www.duckdns.org/update?domains=${SUBDOMAIN}&token=${TOKEN}&ip=" | curl -k -s -o ~/duckdns/duck.log -K -
EOF

chmod +x ~/duckdns/duck.sh
~/duckdns/duck.sh

# ตั้งค่า cron job สำหรับการอัปเดต Duck DNS ทุก 5 นาที
(crontab -l 2>/dev/null || echo "") | grep -v 'duck.sh' | { cat; echo "*/5 * * * * ~/duckdns/duck.sh"; } | crontab -

# สร้างไฟล์การตั้งค่า Nginx
echo "กำลังสร้างการตั้งค่า Nginx..."
sudo tee /etc/nginx/sites-available/goldpredict > /dev/null << EOF
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN};

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # สำหรับไฟล์สถิต (ถ้ามี)
    location /static/ {
        alias ${APP_DIR}/static/;
    }

    location /media/ {
        alias ${APP_DIR}/media/;
    }
}
EOF

# เปิดใช้งานไซต์
echo "กำลังเปิดใช้งานไซต์..."
sudo ln -s /etc/nginx/sites-available/goldpredict /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx

# รอให้ DNS พร้อม (ส่วนใหญ่จะเร็วมาก แต่รอสักครู่เพื่อความแน่ใจ)
echo "กำลังรอให้ DNS record มีผล... (30 วินาที)"
sleep 30

# รับ SSL Certificate จาก Let's Encrypt
echo "กำลังขอใบรับรอง SSL จาก Let's Encrypt..."
sudo certbot --nginx -d ${DOMAIN} --non-interactive --agree-tos --email admin@${DOMAIN} --redirect

# ตั้งค่า cron job สำหรับการต่ออายุอัตโนมัติ (Certbot ตั้งค่าให้เองแล้ว แต่ตรวจสอบให้แน่ใจ)
echo "กำลังตรวจสอบการตั้งค่าการต่ออายุอัตโนมัติ..."
sudo systemctl status certbot.timer

# รีสตาร์ท Docker Compose ถ้าใช้งาน
if [ -f docker-compose.yml ]; then
    echo "กำลังรีสตาร์ท Docker..."
    docker-compose down
    docker-compose up -d
fi

# สร้างสคริปต์ตรวจสอบและอัปเดตโดยอัตโนมัติทุกวัน
cat > ~/check_services.sh << EOF
#!/bin/bash

# ตรวจสอบว่า Duck DNS update ทำงานอยู่หรือไม่
if ! crontab -l | grep -q 'duck.sh'; then
    echo "Duck DNS cron job ไม่พบ... กำลังเพิ่ม..."
    (crontab -l 2>/dev/null || echo "") | { cat; echo "*/5 * * * * ~/duckdns/duck.sh"; } | crontab -
fi

# ตรวจสอบว่า Nginx ทำงานอยู่หรือไม่
if ! systemctl is-active --quiet nginx; then
    echo "Nginx ไม่ทำงาน... กำลังรีสตาร์ท..."
    sudo systemctl restart nginx
fi

# ตรวจสอบว่า Docker Compose ทำงานอยู่หรือไม่ (ถ้ามี)
if [ -f ${APP_DIR}/docker-compose.yml ]; then
    if ! docker ps | grep -q "app"; then
        echo "Docker containers ไม่ทำงาน... กำลังรีสตาร์ท..."
        cd ${APP_DIR} && docker-compose up -d
    fi
fi
EOF

chmod +x ~/check_services.sh

# เพิ่ม cron job เพื่อตรวจสอบบริการทุกวัน
(crontab -l 2>/dev/null || echo "") | grep -v 'check_services.sh' | { cat; echo "0 4 * * * ~/check_services.sh >> ~/service_checks.log 2>&1"; } | crontab -

echo "=========================================================="
echo "การตั้งค่าเสร็จสมบูรณ์!"
echo "เว็บไซต์ของคุณเข้าถึงได้ที่: https://${DOMAIN}"
echo ""
echo "ข้อมูลสำคัญ:"
echo "- Duck DNS จะอัปเดตทุก 5 นาที"
echo "- Let's Encrypt จะต่ออายุโดยอัตโนมัติก่อนหมดอายุ (ทุก 90 วัน)"
echo "- ระบบตรวจสอบจะรันทุกวันเวลาตี 4 เพื่อให้แน่ใจว่าทุกอย่างทำงานปกติ"
echo "- บันทึกไฟล์ setup_duckdns_https.sh นี้ไว้ใช้ในอนาคตถ้าจำเป็น"
echo "=========================================================="