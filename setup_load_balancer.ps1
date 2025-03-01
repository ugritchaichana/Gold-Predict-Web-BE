# ตั้งค่าตัวแปร
$INSTANCE_NAME = "web-server-20250224-134718"
$ZONE = "asia-southeast1-a"
$EXTERNAL_IP = "35.197.132.241"
$DOMAIN = "${EXTERNAL_IP}.nip.io"

Write-Host "Setting up Load Balancer for: $INSTANCE_NAME"
Write-Host "External IP: $EXTERNAL_IP"
Write-Host "Domain will be: $DOMAIN"

# 1. สร้าง health check (ทำงานได้แล้ว)
Write-Host "1. Using existing health check..."
# gcloud compute health-checks create http django-health-check `
#    --port=80 `
#    --request-path=/health/ `
#    --check-interval=30s `
#    --timeout=10s

# 2. สร้าง firewall rule เพื่อให้ health check เข้าถึงได้ (แก้ไข source ranges)
Write-Host "2. Creating firewall rule for health checks..."
gcloud compute firewall-rules create allow-health-checks `
    --network=default `
    --action=allow `
    --direction=ingress `
    --source-ranges="130.211.0.0/22,35.191.0.0/16" `
    --rules=tcp:80

# 3. ใช้ instance group ที่มีอยู่
Write-Host "3. Using existing instance group..."
# gcloud compute instance-groups unmanaged create django-instance-group `
#    --zone=$ZONE

# 4. ใช้ instance ที่มีอยู่ในกลุ่ม
Write-Host "4. Using existing instance in group..."
# gcloud compute instance-groups unmanaged add-instances django-instance-group `
#    --instances=$INSTANCE_NAME `
#    --zone=$ZONE

# 5. ใช้ backend service ที่มีอยู่
Write-Host "5. Using existing backend service..."
# gcloud compute backend-services create django-backend-service `
#    --protocol=HTTP `
#    --port-name=http `
#    --health-checks=django-health-check `
#    --global

# 6. ใช้กลุ่ม instance ที่มีอยู่ใน backend service
Write-Host "6. Using existing backend in service..."
# gcloud compute backend-services add-backend django-backend-service `
#    --instance-group=django-instance-group `
#    --instance-group-zone=$ZONE `
#    --global

# 7. ใช้ URL map ที่มีอยู่
Write-Host "7. Using existing URL map..."
# gcloud compute url-maps create django-url-map `
#    --default-service=django-backend-service

# 8. สร้าง SSL certificate (แก้ไขคำสั่ง)
Write-Host "8. Creating SSL certificate..."
gcloud compute ssl-certificates create django-ssl-cert `
    --global `
    --domains=$DOMAIN

# 9. สร้าง HTTPS target proxy
Write-Host "9. Creating HTTPS proxy..."
gcloud compute target-https-proxies create django-https-proxy `
    --url-map=django-url-map `
    --ssl-certificates=django-ssl-cert

# 10. สร้าง forwarding rule
Write-Host "10. Creating forwarding rule..."
gcloud compute forwarding-rules create django-https-rule `
    --global `
    --target-https-proxy=django-https-proxy `
    --ports=443

# แสดง URL ที่สามารถใช้งานได้
Write-Host "======================================"
Write-Host "Setup complete!"
Write-Host "Your HTTPS URL: https://$DOMAIN"
Write-Host "======================================"
Write-Host "Note: It may take 15-30 minutes for the SSL certificate to be provisioned and active."
Write-Host "You can check certificate status with: gcloud compute ssl-certificates describe django-ssl-cert --global"