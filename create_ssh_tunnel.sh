#!/bin/bash

# สคริปต์สร้าง SSH Tunnel สำหรับ PostgreSQL
# ใช้งาน: ./create_ssh_tunnel.sh [local_port]

LOCAL_PORT=${1:-15432}  # port ใน local machine (default: 15432)
REMOTE_HOST="127.0.0.1"
REMOTE_PORT="5432"
SERVER_IP="3.1.201.90"
SERVER_USER="ubuntu"

echo "🚇 สร้าง SSH Tunnel สำหรับ PostgreSQL..."
echo "======================================"
echo "Local Port: $LOCAL_PORT"
echo "Remote: $REMOTE_HOST:$REMOTE_PORT"
echo "Server: $SERVER_USER@$SERVER_IP"
echo ""

# ตรวจสอบว่า port ว่างหรือไม่
if ss -tuln | grep ":$LOCAL_PORT " >/dev/null; then
    echo "❌ Port $LOCAL_PORT ถูกใช้งานอยู่แล้ว"
    echo "💡 ลองใช้ port อื่น: $0 15433"
    exit 1
fi

echo "🔄 กำลังสร้าง SSH Tunnel..."
echo "กด Ctrl+C เพื่อหยุด tunnel"
echo ""

# สร้าง SSH tunnel
ssh -L $LOCAL_PORT:$REMOTE_HOST:$REMOTE_PORT $SERVER_USER@$SERVER_IP -N

echo ""
echo "🏁 SSH Tunnel ถูกปิดแล้ว"
