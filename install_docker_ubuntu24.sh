#!/bin/bash

# สคริปต์สำหรับติดตั้ง Docker และ Docker Compose เวอร์ชั่นที่เสถียร
# สำหรับ Ubuntu 24.04 LTS (2025)

echo "🚀 กำลังติดตั้ง Docker เวอร์ชั่นเสถียรสำหรับ Ubuntu 24.04..."

# อัปเดตระบบ
sudo apt update && sudo apt upgrade -y

# ติดตั้ง dependencies
sudo apt install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    apt-transport-https \
    software-properties-common

# เพิ่ม Docker GPG key
sudo mkdir -m 0755 -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# เพิ่ม Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# อัปเดต package index
sudo apt update

# ติดตั้ง Docker Engine เวอร์ชั่นเสถียร
# Docker Engine 26.1.4 (LTS) - เสถียรมากสำหรับ production
sudo apt install -y \
    docker-ce=5:26.1.4-1~ubuntu.24.04~noble \
    docker-ce-cli=5:26.1.4-1~ubuntu.24.04~noble \
    containerd.io=1.7.18-1 \
    docker-buildx-plugin=0.14.1-1~ubuntu.24.04~noble

# กำหนดไม่ให้อัปเดตอัตโนมัติ (เพื่อความเสถียร)
sudo apt-mark hold docker-ce docker-ce-cli containerd.io docker-buildx-plugin

# ติดตั้ง Docker Compose v2.27.1 (เสถียรมาก)
sudo curl -L "https://github.com/docker/compose/releases/download/v2.27.1/docker-compose-$(uname -s)-$(uname -m)" \
    -o /usr/local/bin/docker-compose

# ให้สิทธิ์ execute
sudo chmod +x /usr/local/bin/docker-compose

# สร้าง symlink สำหรับ docker-compose
sudo ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

# เพิ่ม user ปัจจุบันเข้า docker group
sudo usermod -aG docker $USER

# เริ่ม Docker service
sudo systemctl enable docker
sudo systemctl start docker

# ตรวจสอบเวอร์ชั่น
echo "✅ การติดตั้งเสร็จสิ้น!"
echo ""
echo "🔍 ตรวจสอบเวอร์ชั่นที่ติดตั้ง:"
docker --version
docker-compose --version
containerd --version

echo ""
echo "⚠️  คำเตือน: ต้อง logout และ login ใหม่เพื่อให้ docker group มีผล"
echo "หรือรันคำสั่ง: newgrp docker"

echo ""
echo "🧪 ทดสอบการทำงาน:"
echo "docker run hello-world"
