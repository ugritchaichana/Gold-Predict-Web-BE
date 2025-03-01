#!/bin/bash

# สร้าง firewall rule เพื่ออนุญาตการเข้าถึงพอร์ต 80 (HTTP)
gcloud compute firewall-rules create allow-http \
  --direction=INGRESS \
  --action=ALLOW \
  --rules=tcp:80 \
  --source-ranges=0.0.0.0/0

# สร้าง firewall rule เพื่ออนุญาตการเข้าถึงพอร์ต 443 (HTTPS)
gcloud compute firewall-rules create allow-https \
  --direction=INGRESS \
  --action=ALLOW \
  --rules=tcp:443 \
  --source-ranges=0.0.0.0/0

echo "Firewall rules created successfully!"