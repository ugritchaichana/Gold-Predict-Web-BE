#!/bin/bash

# สคริปต์ตั้งค่า HTTPS ด้วย Let's Encrypt
# ใช้งาน: ./setup_https.sh yourdomain.com

if [ "$#" -ne 1 ]; then
    echo "กรุณาระบุโดเมนเนม"
    echo "การใช้งาน: $0 yourdomain.com"
    exit 1
fi

DOMAIN=$1

# อัปเดตระบบ
echo "กำลังอัปเดตระบบ..."
sudo apt update
sudo apt upgrade -y

# ติดตั้ง Nginx และ Certbot
echo "กำลังติดตั้ง Nginx และ Certbot..."
sudo apt install nginx certbot python3-certbot-nginx -y

# สร้างไฟล์การตั้งค่า Nginx
echo "กำลังสร้างการตั้งค่า Nginx..."
sudo tee /etc/nginx/sites-available/goldpredict > /dev/null << EOF
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN www.$DOMAIN;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # สำหรับไฟล์สถิต (ปรับเส้นทางตามความเหมาะสม)
    location /static/ {
        alias $(pwd)/static/;
    }

    location /media/ {
        alias $(pwd)/media/;
    }
}
EOF

# เปิดใช้งานไซต์
echo "กำลังเปิดใช้งานไซต์..."
sudo ln -s /etc/nginx/sites-available/goldpredict /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx

# รับ SSL Certificate
echo "กำลังรับ SSL Certificate จาก Let's Encrypt..."
sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN

# รีสตาร์ท Docker Compose
echo "กำลังรีสตาร์ท Docker..."
docker-compose down
docker-compose up -d

echo "การตั้งค่า HTTPS เสร็จสมบูรณ์!"
echo "เว็บไซต์ของคุณตอนนี้ปลอดภัยด้วย HTTPS ที่ https://$DOMAIN"
echo ""
echo "การต่ออายุใบรับรองจะเกิดขึ้นโดยอัตโนมัติทุก 90 วัน"
echo "คุณสามารถทดสอบการต่ออายุด้วยคำสั่ง: sudo certbot renew --dry-run" 