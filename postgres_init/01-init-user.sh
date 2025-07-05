#!/bin/bash
set -e

# สคริปต์ initialization สำหรับ PostgreSQL
echo "🔧 PostgreSQL Initialization Script..."

# สร้าง user และ database (ถ้ายังไม่มี)
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- ตรวจสอบและสร้าง user ถ้ายังไม่มี
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'goldpredict') THEN
            CREATE USER goldpredict WITH ENCRYPTED PASSWORD 'goldpredict';
        END IF;
    END
    \$\$;

    -- ให้สิทธิ์ต่างๆ
    GRANT ALL PRIVILEGES ON DATABASE goldpredict_db TO goldpredict;
    GRANT ALL PRIVILEGES ON SCHEMA public TO goldpredict;
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO goldpredict;
    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO goldpredict;
    GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO goldpredict;

    -- ตั้งค่า default privileges สำหรับ objects ที่จะสร้างในอนาคต
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO goldpredict;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO goldpredict;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO goldpredict;

    -- แสดงข้อมูล users
    \du
EOSQL

echo "✅ PostgreSQL initialization completed!"
