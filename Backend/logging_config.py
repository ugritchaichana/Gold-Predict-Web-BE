import os
from pathlib import Path

# Base directory of the Django project
BASE_DIR = Path(__file__).resolve().parent.parent

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file_debug': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'debug.log'),
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 3,  # เก็บไฟล์สำรอง 3 ไฟล์
            'formatter': 'verbose',
        },
        'file_error': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'error.log'),
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 3,  # เก็บไฟล์สำรอง 3 ไฟล์
            'formatter': 'verbose',
        },
        'file_django': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 2,  # เก็บไฟล์สำรอง 2 ไฟล์
            'formatter': 'verbose',
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console'],
    },
    'loggers': {
        'django': {
            'handlers': ['file_django'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['file_error'],
            'level': 'ERROR',
            'propagate': False,
        },
        'gold': {  # สำหรับ app ชื่อ gold
            'handlers': ['file_debug', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'predicts': {  # สำหรับ app ชื่อ predicts
            'handlers': ['file_debug', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'currency': {  # สำหรับ app ชื่อ currency
            'handlers': ['file_debug', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
