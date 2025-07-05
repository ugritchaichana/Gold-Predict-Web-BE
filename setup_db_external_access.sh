#!/bin/bash

# สคริปต์ตั้งค่า Firewall สำหรับ PostgreSQL External Access
echo "🔥 ตั้งค่า Firewall สำหรับ PostgreSQL..."

# ตรวจสอบว่าใช้ ufw หรือ iptables
if command -v ufw >/dev/null 2>&1; then
    echo "📋 ใช้ UFW Firewall"
    
    # เปิด port 5432 สำหรับ PostgreSQL
    echo "🔓 เปิด port 5432 สำหรับ PostgreSQL..."
    sudo ufw allow 5432/tcp comment "PostgreSQL Database"
    
    # แสดงสถานะ
    echo "📊 สถานะ UFW:"
    sudo ufw status numbered
    
elif command -v iptables >/dev/null 2>&1; then
    echo "📋 ใช้ iptables"
    
    # เปิด port 5432
    echo "🔓 เปิด port 5432 สำหรับ PostgreSQL..."
    sudo iptables -A INPUT -p tcp --dport 5432 -j ACCEPT
    
    # บันทึกการตั้งค่า (Ubuntu/Debian)
    if command -v iptables-save >/dev/null 2>&1; then
        sudo iptables-save > /etc/iptables/rules.v4 2>/dev/null || echo "⚠️ ไม่สามารถบันทึกการตั้งค่า iptables"
    fi
    
    echo "📊 กฎ iptables ปัจจุบัน:"
    sudo iptables -L INPUT -n --line-numbers | grep 5432
    
else
    echo "⚠️ ไม่พบ Firewall tools (ufw หรือ iptables)"
fi

echo ""
echo "⚠️ คำเตือนความปลอดภัย:"
echo "================================"
echo "🔸 การเปิด PostgreSQL port ให้ external access มีความเสี่ยง"
echo "🔸 ควรตั้งค่า IP whitelist หรือใช้ SSH tunnel แทน"
echo "🔸 ตรวจสอบให้แน่ใจว่า password ของ database แข็งแรง"
echo ""

# แสดงข้อมูลการเชื่อมต่อ
echo "📝 ข้อมูลสำหรับเชื่อมต่อ DBeaver:"
echo "================================="
echo "Host: 3.1.201.90"
echo "Port: 5432"
echo "Database: goldpredict_db"
echo "Username: goldpredict"
echo "Password: goldpredict"
echo ""

echo "✅ การตั้งค่าเสร็จสิ้น!"
