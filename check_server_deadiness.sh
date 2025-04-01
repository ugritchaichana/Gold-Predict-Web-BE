#!/bin/bash

# สคริปต์ตรวจสอบความพร้อมของเซิร์ฟเวอร์ Debian GCP สำหรับการติดตั้ง HTTPS
# ใช้งาน: ./check_server_readiness.sh

echo "=============================================="
echo "  ตรวจสอบความพร้อมของเซิร์ฟเวอร์ Debian GCP"
echo "=============================================="

# ตรวจสอบระบบปฏิบัติการ
echo -e "\n[1] ข้อมูลระบบปฏิบัติการ:"
echo "----------------------------------------------"
if [ -f /etc/os-release ]; then
    cat /etc/os-release | grep -E "^(NAME|VERSION)="
else
    echo "❌ ไม่สามารถระบุระบบปฏิบัติการได้"
fi

# ตรวจสอบการเชื่อมต่ออินเทอร์เน็ต
echo -e "\n[2] การเชื่อมต่ออินเทอร์เน็ต:"
echo "----------------------------------------------"
if ping -c 1 google.com &> /dev/null; then
    echo "✅ เชื่อมต่ออินเทอร์เน็ตได้"
else
    echo "❌ ไม่สามารถเชื่อมต่ออินเทอร์เน็ตได้"
fi

# ตรวจสอบทรัพยากรของระบบ
echo -e "\n[3] ทรัพยากรของระบบ:"
echo "----------------------------------------------"
echo "CPU:"
lscpu | grep -E "^(Model name|Architecture|CPU\(s\))"
echo -e "\nหน่วยความจำ:"
free -h
echo -e "\nพื้นที่ดิสก์:"
df -h /

# ตรวจสอบโปรแกรมที่จำเป็น
echo -e "\n[4] โปรแกรมที่จำเป็น:"
echo "----------------------------------------------"
required_packages=("nginx" "docker" "docker-compose" "python3" "certbot" "curl" "git")

for pkg in "${required_packages[@]}"; do
    echo -n "ตรวจสอบ $pkg: "
    if command -v $pkg &> /dev/null; then
        echo "✅ ติดตั้งแล้ว $(($pkg --version 2>/dev/null || echo 'ไม่สามารถแสดงเวอร์ชันได้'))"
    else
        echo "❌ ยังไม่ได้ติดตั้ง"
    fi
done

# ตรวจสอบพอร์ตและบริการที่กำลังทำงาน
echo -e "\n[5] พอร์ตและบริการที่กำลังทำงาน:"
echo "----------------------------------------------"
if command -v netstat &> /dev/null; then
    netstat -tulpn | grep -E ":(80|443|8000)" || echo "ไม่มีบริการที่ใช้พอร์ต 80, 443, หรือ 800>
elif command -v ss &> /dev/null; then
    ss -tulpn | grep -E ":(80|443|8000)" || echo "ไม่มีบริการที่ใช้พอร์ต 80, 443, หรือ 8000"
else
    echo "❌ ไม่พบคำสั่ง netstat หรือ ss"
fi

# ตรวจสอบ firewall rules
echo -e "\n[6] การตั้งค่า Firewall:"
echo "----------------------------------------------"
if command -v ufw &> /dev/null; then
    ufw status
elif command -v iptables &> /dev/null; then
    iptables -L -n
else
    echo "ไม่พบการตั้งค่า firewall (ufw หรือ iptables)"
fi

# ตรวจสอบ GCP firewall rules หากเป็น GCP
echo -e "\n[7] GCP Firewall Rules:"
echo "----------------------------------------------"
if curl -s -H "Metadata-Flavor: Google" http://metadata.google.internal &> /dev/null; t>
    echo "ตรวจพบว่าเป็น GCP VM"
    if command -v gcloud &> /dev/null; then
        gcloud compute firewall-rules list --format="table(
            name,
            network,
            direction,
            sourceRanges.list():label=SRC_RANGES,
            allowed[].map().firewall_rule().list():label=ALLOW,
            targetTags.list():label=TARGET_TAGS
        )" 2>/dev/null || echo "❌ ไม่สามารถแสดง GCP firewall rules ได้ (อาจต้องการสิทธิ์เพิ่มเ>
    else
        echo "❌ ไม่ได้ติดตั้ง gcloud CLI"
    fi
else
    echo "ไม่ใช่ GCP VM หรือไม่สามารถเข้าถึง GCP metadata ได้"
fi

# ตรวจสอบการตั้งค่า DNS สำหรับ Duck DNS
echo -e "\n[8] การตั้งค่า Duck DNS:"
echo "----------------------------------------------"
if [ -f .env ] && grep -q "DUCK_DNS_DOMAIN" .env && grep -q "DUCK_DNS_TOKEN" .env; then
    DOMAIN=$(grep "DUCK_DNS_DOMAIN" .env | cut -d= -f2)
    TOKEN=$(grep "DUCK_DNS_TOKEN" .env | cut -d= -f2)
    echo "พบการตั้งค่า Duck DNS ในไฟล์ .env:"
    echo "- โดเมน: $DOMAIN"
    echo "- โทเค็น: ${TOKEN:0:5}***${TOKEN: -5} (เซ็นเซอร์)"
    
    echo -e "\nทดสอบการอัปเดต Duck DNS:"
    UPDATE_RESULT=$(curl -s "https://www.duckdns.org/update?domains=${DOMAIN%%.*}&token>
    if [ "$UPDATE_RESULT" = "OK" ]; then
        echo "✅ การอัปเดต Duck DNS สำเร็จ!"
    else
        echo "❌ การอัปเดต Duck DNS ล้มเหลว: $UPDATE_RESULT"
    fi
    
    echo -e "\nตรวจสอบการแก้ไข DNS:"
    dig +short $DOMAIN || nslookup $DOMAIN | grep -A 1 "Name:" | tail -n 1 || echo "❌ >
else
    echo "❌ ไม่พบการตั้งค่า Duck DNS ในไฟล์ .env"
fi


# ตรวจสอบโปรเจ็ค Django
echo -e "\n[9] โปรเจ็ค Django:"
echo "----------------------------------------------"
if [ -f manage.py ]; then
    echo "✅ พบไฟล์ manage.py (โปรเจ็ค Django)"
    if grep -q "ALLOWED_HOSTS" $(find . -name settings.py | head -n 1 2>/dev/null) 2>/d>
        echo "✅ พบการตั้งค่า ALLOWED_HOSTS ในไฟล์ settings.py"
    else
        echo "❌ ไม่พบการตั้งค่า ALLOWED_HOSTS ในไฟล์ settings.py"
    fi
else
    echo "❌ ไม่พบไฟล์ manage.py (อาจไม่ใช่โปรเจ็ค Django หรืออยู่ผิดไดเร็กทอรี)"
fi

# ตรวจสอบการตั้งค่า Docker Compose
echo -e "\n[10] การตั้งค่า Docker Compose:"
echo "----------------------------------------------"
if [ -f docker-compose.yml ]; then
    echo "✅ พบไฟล์ docker-compose.yml"
    grep -n "ports:" -A3 docker-compose.yml
else
    echo "❌ ไม่พบไฟล์ docker-compose.yml"
fi

# สรุปและคำแนะนำ
echo -e "\n=============================================="
echo "                  สรุปผล"
echo "=============================================="
echo "* หากไม่พบ Nginx, Certbot: ต้องติดตั้งด้วย 'sudo apt install nginx certbot python3-cert>
echo "* หากไม่พบ Docker, Docker Compose: ต้องติดตั้งตามคำแนะนำใน https://docs.docker.com/eng>
echo "* ตรวจสอบว่าพอร์ต 80 และ 443 เปิดใน GCP Firewall Rules"
echo "* หากตรวจสอบและแก้ไขตามคำแนะนำข้างต้นแล้ว ให้รันสคริปต์ setup_duckdns_https.sh เพื่อตั้งค่า HT>
echo "=============================================="