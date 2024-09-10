# Backend/celery.py

from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# ตั้งค่า default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Backend.settings')

app = Celery('Backend')

# ใช้ชื่อการตั้งค่าของ Django สำหรับการตั้งค่า Celery
app.config_from_object('django.conf:settings', namespace='CELERY')

# อัตโนมัตินำเข้า tasks จากทุก module ที่กำหนดใน Django apps
app.autodiscover_tasks()
