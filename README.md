# Gold Predict Web Backend

คู่มือนี้เขียนใหม่ให้ตรงตามที่ต้องการ: setup ตั้งแต่เริ่มจนใช้งาน backend ได้จริง 2 แบบ

1. `venv` + Docker เฉพาะ `db + redis`
2. Full Docker (`backend + db + redis`)

> สำคัญ: โปรเจ็กต์นี้เช็กการเชื่อมต่อ PostgreSQL และ Redis ก่อนรันคำสั่ง Django ใน `manage.py` ดังนั้น DB/Redis ต้องพร้อมก่อน `migrate` และ `runserver`

---

## 0) เตรียมเครื่อง

ต้องมี:
- Python `3.12.x`
- Docker Desktop (Compose v2)
- Git

ตรวจเวอร์ชัน:

```powershell
py --version
docker --version
docker compose version
git --version
```

---

## 1) เตรียมโปรเจ็กต์และไฟล์ `.env`

### Step 1.1 Clone

```powershell
git clone https://github.com/ugritchaichana/Gold-Predict-Web-BE.git
cd Gold-Predict-Web-BE
```

### Step 1.2 สร้าง `.env`

คัดลอกจากตัวอย่าง:

```powershell
Copy-Item .env.example .env
```

แล้วแก้ `.env` ให้มีอย่างน้อย:

```env
SECRET_KEY=change-this-secret-key
DEBUG=true
RENDER=false
DJANGO_SETTINGS_MODULE=Backend.settings

DB_NAME=goldpredict_db
DB_USER=goldpredict_user
DB_PASSWORD=goldpredict_password
DB_PORT=5432

REDIS_PORT=6379
LOG_LEVEL=INFO

GCS_SERVICE_ACCOUNT_KEY=
GCS_BUCKET_NAME=
GCP_PROJECT_ID=
```

---

## 2) แบบที่ 1: `venv` + Docker (`db + redis`)

Backend รันบนเครื่องเรา (venv), แต่ PostgreSQL/Redis รันใน Docker

### Step 2.1 ตั้ง `DB_HOST` และ `REDIS_HOST` ให้ชี้มาที่ localhost

ใน `.env`:

```env
DB_HOST=127.0.0.1
REDIS_HOST=127.0.0.1
```

### Step 2.2 เปิดเฉพาะ DB และ Redis ด้วย Docker

```powershell
docker compose up -d postgresql redis
docker compose ps
```

### Step 2.3 (ทางเลือก) Restore DB จากไฟล์ backup ที่มีอยู่

ถ้าต้องการใช้ข้อมูลเดิมจาก backup (`MigrateDB/dump-goldpredict_db-202603162348.sql`) ให้ restore ก่อนรัน backend:

```powershell
$cid = docker compose ps -q postgresql
docker cp ".\MigrateDB\dump-goldpredict_db-202603162348.sql" "$cid`:/tmp/dump-goldpredict_db.dump"
docker compose exec -T postgresql pg_restore -U goldpredict -d goldpredict_db --clean --if-exists --no-owner --no-privileges /tmp/dump-goldpredict_db.dump
```

หมายเหตุสำคัญ:
- ไฟล์ `dump-goldpredict_db-202603162348.sql` เป็น PostgreSQL custom-format dump จึงต้องใช้ `pg_restore` (ไม่ใช่ `psql`)
- ให้ใช้ user ที่เป็น owner ของตารางเดิม (ในโปรเจ็กต์นี้คือ `goldpredict`) เพื่อให้ `--clean` ทำงานได้ครบ

หลัง restore:
- ถ้า backup มี schema+data ครบและตรงกับโค้ดปัจจุบัน สามารถรัน backend ต่อได้
- แนะนำให้รัน `py manage.py migrate` อยู่ดีเพื่อ sync migration ใหม่ (คำสั่งนี้ปลอดภัยและจะไม่แก้ซ้ำถ้าไม่มี migration ค้าง)

### Step 2.4 สร้างและเปิด venv

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 2.5 migrate และรัน backend

```powershell
py manage.py migrate
py manage.py runserver
```

### Step 2.6 ทดสอบว่าใช้งานได้

```powershell
curl http://127.0.0.1:8000/health/
```

ผลที่ถูกต้อง: `OK`

### Step 2.7 หยุดระบบ

- หยุด backend: `Ctrl + C`
- ปิด container DB/Redis:

```powershell
docker compose stop postgresql redis
```

---

## 3) แบบที่ 2: Full Docker (`backend + db + redis`)

ทุก service รันใน Docker ทั้งหมด

### Step 3.1 ตั้งค่า `.env` สำหรับ Docker

ใน `.env` ให้มีค่าพื้นฐานเดิม และใช้ host แบบ service name:

```env
DB_HOST=postgresql
REDIS_HOST=redis
```

### Step 3.2 สั่งรันทั้งหมด

```powershell
docker compose up --build -d
docker compose ps
```

หมายเหตุ: โหมด Full Docker ของโปรเจ็กต์นี้ตั้งค่าให้ service `app` รัน `python manage.py migrate` อัตโนมัติก่อน `runserver`

### Step 3.3 (ทางเลือก) Restore DB จาก backup

ถ้าต้องการใช้ข้อมูลเดิม ให้ restore หลัง DB ขึ้นแล้ว:

```powershell
$cid = docker compose ps -q postgresql
docker cp ".\MigrateDB\dump-goldpredict_db-202603162348.sql" "$cid`:/tmp/dump-goldpredict_db.dump"
docker compose exec -T postgresql pg_restore -U goldpredict -d goldpredict_db --clean --if-exists --no-owner --no-privileges /tmp/dump-goldpredict_db.dump
```

ถ้าเจอ `role "goldpredict_user" does not exist` และต้องการสร้างไว้ใช้งานด้วย ให้สั่ง:

```powershell
docker compose exec -T postgresql psql -U goldpredict -d postgres -c "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'goldpredict_user') THEN CREATE ROLE goldpredict_user LOGIN PASSWORD 'goldpredict_password'; END IF; END $$;"
docker compose exec -T postgresql psql -U goldpredict -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE goldpredict_db TO goldpredict_user;"
docker compose exec -T postgresql psql -U goldpredict -d goldpredict_db -c "GRANT ALL ON SCHEMA public TO goldpredict_user; GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO goldpredict_user; GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO goldpredict_user; GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO goldpredict_user; ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO goldpredict_user; ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO goldpredict_user; ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO goldpredict_user;"
```

### Step 3.4 ดู log backend (ถ้าต้องการ)

```powershell
docker compose logs -f app
```

### Step 3.5 ทดสอบว่าใช้งานได้

```powershell
curl http://127.0.0.1:8000/health/
```

ผลที่ถูกต้อง: `OK`

### Step 3.6 หยุดระบบ

```powershell
docker compose down
```

ถ้าต้องการลบข้อมูล DB/Redis ด้วย:

```powershell
docker compose down -v
```

---

## 4) ปัญหาที่เจอบ่อย

- `Failed to connect to Database`
  - ตรวจ `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
  - ตรวจว่า container `postgresql` ขึ้นแล้ว

- `Failed to connect to Redis`
  - ตรวจ `REDIS_HOST`, `REDIS_PORT`
  - ตรวจว่า container `redis` ขึ้นแล้ว

- Full Docker แล้ว app ไม่ขึ้น
  - ดู log ด้วย `docker compose logs -f app postgresql redis`

- `The input is a PostgreSQL custom-format dump`
  - ใช้ `pg_restore` แทน `psql`

- `must be owner of table ...` ตอน restore
  - ให้ restore ด้วย user owner (`goldpredict`) และใช้ `--clean --if-exists`

---

## 5) คำสั่งสรุปแบบเร็ว

### โหมด 1: venv + docker db/redis

```powershell
docker compose up -d postgresql redis
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
py manage.py migrate
py manage.py runserver
```

### โหมด 2: full docker

```powershell
docker compose up --build -d
docker compose logs -f app
```

