#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import time
from django.db import connections
import redis
from django.core.management import execute_from_command_line


def check_redis_connection():
    try:
        r = redis.StrictRedis(host=os.getenv('REDIS_HOST',
                                            '35.197.132.241'
                                            #  'localhost'
                                            ), port=int(os.getenv('REDIS_PORT', 6379)), db=1)
        r.ping()
        print("✅ Redis connection successful!")
    except redis.ConnectionError as e:
        print("❌ Failed to connect to Redis:", e)
        sys.exit(1)


def check_database_connection():
    try:
        # เช็คการเชื่อมต่อกับฐานข้อมูล
        connection = connections['default']
        connection.ensure_connection()
        print("✅ Database connection successful!")
    except Exception as e:
        print("❌ Failed to connect to Database:", e)
        sys.exit(1)


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Backend.settings')
    
    # เช็คการเชื่อมต่อก่อนที่ Django จะเริ่มทำงาน
    print("🔄 Checking connections...")
    check_database_connection()
    check_redis_connection()

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
