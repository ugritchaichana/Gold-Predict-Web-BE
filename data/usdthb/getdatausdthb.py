import random
import time
import json
import os
import ssl
import socket
from datetime import datetime, timezone, timedelta
import cloudscraper
import requests
import logging
from urllib.parse import urlparse
import backoff
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import sys

# ตั้งค่า logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("usdthb_fetch.log")
    ]
)
logger = logging.getLogger(__name__)

# เพิ่มการแสดงผลทาง console
def show_message(message):
    """แสดงข้อความทั้งที่ console และ log"""
    print(f"[USD/THB] {message}")
    logger.info(message)

# ---- ปรับแต่งการตั้งค่า -----
# IP Checking - ตรวจสอบแค่ตอนเริ่มต้นและเมื่อจำเป็น
IP_CHECK_INTERVAL = 300  # 5 นาที
last_ip_check = 0
current_ip = None

# Simplified proxy system
USE_PROXY = False  # ปิดการใช้ proxy โดยค่าเริ่มต้น เพื่อความเร็ว
PROXY_LIST = []
PROXY_INDEX = 0

# ลดจำนวนข้อมูลที่ดึงต่อครั้งเพื่อหลีกเลี่ยงการถูกบล็อก
MAX_ITEMS = 1000  
RESOLUTION_MINUTES = 60
SECONDS_PER_ITEM = RESOLUTION_MINUTES * 60
MAX_DELTA_SECONDS = MAX_ITEMS * SECONDS_PER_ITEM
MAX_DELTA = timedelta(seconds=MAX_DELTA_SECONDS)

# Maximum retries
MAX_RETRIES = 3
RETRY_DELAY = 2  # วินาที

# ฟังก์ชันตรวจสอบ IP - ใช้ caching เพื่อลดการเรียกใช้งาน
def get_my_ip():
    """ฟังก์ชันตรวจสอบ IP แบบ cached เพื่อประสิทธิภาพ"""
    global last_ip_check, current_ip
    
    # ใช้ค่าเดิมถ้ายังไม่เกินเวลาที่กำหนด
    if current_ip and time.time() - last_ip_check < IP_CHECK_INTERVAL:
        return current_ip
    
    try:
        show_message("กำลังตรวจสอบ IP ปัจจุบัน...")
        response = requests.get('https://api.ipify.org', timeout=3)
        if response.status_code == 200:
            current_ip = response.text.strip()
            last_ip_check = time.time()
            show_message(f"IP ปัจจุบัน: {current_ip}")
            return current_ip
    except:
        show_message("ไม่สามารถเชื่อมต่อกับ api.ipify.org ได้")
        pass
    
    # ถ้าล้มเหลว ลองบริการสำรอง
    try:
        response = requests.get('https://ifconfig.me/ip', timeout=3)
        if response.status_code == 200:
            current_ip = response.text.strip()
            last_ip_check = time.time()
            show_message(f"IP ปัจจุบัน (สำรอง): {current_ip}")
            return current_ip
    except:
        # ถ้าล้มเหลวทั้งหมด ใช้ค่าเดิมหรือค่าว่าง
        if not current_ip:
            current_ip = "unknown"
        show_message(f"ไม่สามารถตรวจสอบ IP ได้ ใช้ค่า: {current_ip}")
        return current_ip

# ----- STEALTH CONFIGURATIONS -----

# User agents ที่หลากหลาย
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0"
]

# Referrers ที่หลากหลาย
REFERRERS = [
    "https://www.investing.com/currencies/usd-thb",
    "https://th.investing.com/currencies/usd-thb",
    "https://www.investing.com/currencies/usd-thb-chart",
    "https://www.google.com/search?q=usd+thb+rate+investing.com"
]

# URLs
URLS = [
    'https://tvc4.investing.com/57c182657e622fb4e391a1c95dbc2589/1742541167/1/1/8/history?symbol=147&resolution={resolution}&from={start}&to={end}',
    'https://tvc4.forexpros.com/57c182657e622fb4e391a1c95dbc2589/1742541167/1/1/8/history?symbol=147&resolution={resolution}&from={start}&to={end}',
    'https://tvc2.investing.com/57c182657e622fb4e391a1c95dbc2589/1742541167/1/1/8/history?symbol=147&resolution={resolution}&from={start}&to={end}'
]

# ----- ฟังก์ชันสร้าง HEADERS ขั้นพื้นฐาน -----

def create_headers():
    """สร้าง headers พื้นฐาน"""
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept-Language': 'en-US,en;q=0.9,th;q=0.8',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Referer': random.choice(REFERRERS),
        'X-Requested-With': 'XMLHttpRequest',
        'Cache-Control': 'no-cache'
    }

# ----- PROXY FUNCTIONS (SIMPLIFIED) -----

def load_proxies_from_file(file_path='proxies.txt'):
    """โหลด proxies จากไฟล์ (ถ้ามี)"""
    global PROXY_LIST
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                PROXY_LIST = [line.strip() for line in f if line.strip()]
            show_message(f"โหลด {len(PROXY_LIST)} proxies จากไฟล์")
        else:
            show_message("ไม่พบไฟล์ proxy")
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการโหลด proxies: {e}")

def toggle_proxy_usage(use_proxy=None):
    """เปิด/ปิดการใช้งาน proxy"""
    global USE_PROXY
    if use_proxy is not None:
        USE_PROXY = use_proxy
    else:
        USE_PROXY = not USE_PROXY
    
    status = "เปิด" if USE_PROXY else "ปิด"
    show_message(f"การใช้งาน proxy: {status}")
    return USE_PROXY

def get_next_proxy():
    """ดึง proxy ถัดไปจากรายการ"""
    global PROXY_INDEX
    if not PROXY_LIST:
        return None
    
    proxy = PROXY_LIST[PROXY_INDEX % len(PROXY_LIST)]
    PROXY_INDEX += 1
    return proxy

def create_session(use_proxy=False):
    """สร้าง session สำหรับ requests"""
    session = requests.Session()
    session.headers.update(create_headers())
    
    if use_proxy and USE_PROXY and PROXY_LIST:
        proxy = get_next_proxy()
        if proxy:
            session.proxies = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }
            logger.debug(f"ใช้ proxy: {proxy}")
    return session

def create_cloudscraper(use_proxy=False):
    """สร้าง cloudscraper session"""
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    scraper.headers.update(create_headers())
    
    if use_proxy and USE_PROXY and PROXY_LIST:
        proxy = get_next_proxy()
        if proxy:
            scraper.proxies = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }
            logger.debug(f"ใช้ cloudscraper proxy: {proxy}")
    return scraper

# ----- MAIN REQUEST FUNCTIONS -----

def make_request(url, max_retries=MAX_RETRIES, use_proxy=False):
    """ส่งคำขอไปยัง URL พร้อมระบบ retry"""
    for attempt in range(max_retries):
        try:
            # สลับวิธีการขอข้อมูลสลับกันไป
            if attempt % 2 == 0:
                show_message(f"ส่งคำขอครั้งที่ {attempt+1} (ใช้ requests)")
                session = create_session(use_proxy)
                response = session.get(url, timeout=10)
            else:
                show_message(f"ส่งคำขอครั้งที่ {attempt+1} (ใช้ cloudscraper)")
                scraper = create_cloudscraper(use_proxy)
                response = scraper.get(url, timeout=10)
                
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get('s') == 'ok':
                        show_message(f"ได้รับข้อมูลสำเร็จ (มีข้อมูล {len(result.get('t', []))} รายการ)")
                    return result
                except json.JSONDecodeError:
                    show_message(f"ไม่สามารถแปลงคำตอบเป็น JSON ได้ (พยายามครั้งที่ {attempt+1}/{max_retries})")
            else:
                show_message(f"สถานะการตอบกลับผิดพลาด: {response.status_code} (พยายามครั้งที่ {attempt+1}/{max_retries})")
                
        except Exception as e:
            show_message(f"เกิดข้อผิดพลาดในการส่งคำขอ: {str(e)} (พยายามครั้งที่ {attempt+1}/{max_retries})")
        
        # รอก่อนลองใหม่
        wait_time = RETRY_DELAY * (attempt + 1)
        show_message(f"รอ {wait_time} วินาทีก่อนลองใหม่...")
        time.sleep(wait_time)
        
        # สลับ proxy ในการลองครั้งถัดไป
        if USE_PROXY and PROXY_LIST:
            get_next_proxy()
    
    show_message(f"ล้มเหลวหลังจากลอง {max_retries} ครั้ง")
    return None

def get_data_chunk(start_ts, end_ts, resolution="60"):
    """ดึงข้อมูลจากช่วงเวลาที่กำหนด"""
    # สลับ URL สุ่ม
    url_template = random.choice(URLS)
    
    # ใส่เวลาปัจจุบันลงไปเพื่อหลีกเลี่ยงแคช
    url = url_template.format(
        resolution=resolution,
        start=start_ts,
        end=end_ts
    )
    
    # แสดงข้อมูลการดึงข้อมูล
    start_time = datetime.fromtimestamp(start_ts, tz=timezone.utc)
    end_time = datetime.fromtimestamp(end_ts, tz=timezone.utc)
    show_message(f"กำลังดึงข้อมูล USD/THB ตั้งแต่ {start_time} ถึง {end_time} (IP: {get_my_ip()})")
    
    # ลอง proxy แล้วค่อยลองแบบไม่มี proxy ถ้า proxy ไม่สำเร็จ
    if USE_PROXY and PROXY_LIST:
        show_message("กำลังลองใช้ proxy...")
        result = make_request(url, use_proxy=True)
        if result and result.get('s') == 'ok':
            return result
        show_message("การใช้ proxy ล้มเหลว ลองใช้การเชื่อมต่อโดยตรง...")    
            
    # ถ้า proxy ไม่สำเร็จหรือไม่ได้ใช้ proxy ให้ลองแบบไม่มี proxy
    return make_request(url, use_proxy=False)

def get_data_usdthb(start_ts, end_ts, use_proxy=False):
    """
    ดึงข้อมูลอัตราแลกเปลี่ยน USD/THB
    
    Args:
        start_ts (int): เวลาเริ่มต้นเป็น timestamp
        end_ts (int): เวลาสิ้นสุดเป็น timestamp
        use_proxy (bool): เปิดใช้งาน proxy หรือไม่
        
    Returns:
        list: รายการข้อมูลอัตราแลกเปลี่ยนในรูปแบบ list ของ dict ที่มี keys: timestamp, open, high, low, close
    """
    # เปิด/ปิดการใช้งาน proxy
    toggle_proxy_usage(use_proxy)
    
    # โหลด proxies จากไฟล์ (ถ้ามี)
    if USE_PROXY:
        load_proxies_from_file()
    
    # แสดง IP ปัจจุบัน
    show_message(f"เริ่มดึงข้อมูล USD/THB (IP: {get_my_ip()})")
    
    # แปลงเวลาให้อยู่ในรูปแบบที่อ่านได้
    start_time = datetime.fromtimestamp(start_ts, tz=timezone.utc)
    end_time = datetime.fromtimestamp(end_ts, tz=timezone.utc)
    show_message(f"ช่วงเวลาที่ต้องการ: {start_time} ถึง {end_time}")
    
    # ตรวจสอบว่าช่วงเวลาสมเหตุสมผลหรือไม่
    current_time = datetime.now(timezone.utc)
    if end_time > current_time:
        end_time = current_time
        end_ts = int(end_time.timestamp())
        show_message(f"ปรับเวลาสิ้นสุดเป็นเวลาปัจจุบัน: {end_time}")
    
    if end_ts <= start_ts:
        show_message("เวลาสิ้นสุดต้องมากกว่าเวลาเริ่มต้น")
        return []
    
    # แบ่งช่วงเวลาเป็นช่วงย่อยๆ
    all_data = []
    delta = end_ts - start_ts
    
    # ถ้าช่วงเวลาสั้น ดึงทีเดียว
    if delta <= MAX_DELTA_SECONDS:
        show_message("ช่วงเวลาสั้น จะดึงข้อมูลในครั้งเดียว")
        result = get_data_chunk(start_ts, end_ts)
        if result and result.get('s') == 'ok':
            # แปลงข้อมูลให้อยู่ในรูปแบบที่เหมาะสม
            processed_data = process_raw_data(result)
            return processed_data
        else:
            show_message("ไม่สามารถดึงข้อมูลได้")
            return []
    
    # ถ้าช่วงเวลายาว แบ่งดึงทีละส่วน
    chunk_results = []
    chunk_size = MAX_DELTA_SECONDS
    chunks = []
    
    current = start_ts
    while current < end_ts:
        next_point = min(current + chunk_size, end_ts)
        chunks.append((current, next_point))
        current = next_point
    
    show_message(f"ช่วงเวลายาว แบ่งการดึงข้อมูลเป็น {len(chunks)} ส่วน")
    
    # ดึงข้อมูลแบบขนานเพื่อความเร็ว
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for start, end in chunks:
            futures.append(executor.submit(get_data_chunk, start, end))
        
        # รวมผลลัพธ์
        for future in as_completed(futures):
            try:
                result = future.result()
                if result and result.get('s') == 'ok':
                    chunk_results.append(result)
                    show_message(f"ดึงข้อมูลส่วนที่ {len(chunk_results)}/{len(chunks)} สำเร็จ")
                else:
                    show_message(f"ดึงข้อมูลส่วนที่ {len(chunk_results)+1}/{len(chunks)} ล้มเหลว")
            except Exception as e:
                show_message(f"เกิดข้อผิดพลาดในการดึงข้อมูล: {str(e)}")
    
    # รวมข้อมูลจากทุกส่วน
    if not chunk_results:
        show_message("ไม่สามารถดึงข้อมูลได้เลย")
        return []
    
    combined = {'t': [], 'o': [], 'h': [], 'l': [], 'c': [], 'v': []}
    for result in chunk_results:
        for key in combined:
            if key in result:
                combined[key].extend(result[key])
    
    # จัดเรียงข้อมูลตามเวลา
    sorted_indices = sorted(range(len(combined['t'])), key=lambda i: combined['t'][i])
    
    for key in combined:
        combined[key] = [combined[key][i] for i in sorted_indices]
    
    show_message(f"ดึงข้อมูลสำเร็จ ได้ {len(combined['t'])} รายการ")
    
    # แปลงข้อมูลให้อยู่ในรูปแบบที่เหมาะสม
    processed_data = process_raw_data(combined)
    return processed_data

def process_raw_data(raw_data):
    """
    แปลงข้อมูลดิบจาก API เป็นรูปแบบ list ของ dictionary
    
    Args:
        raw_data (dict): ข้อมูลดิบที่ได้จาก API ที่มี keys t, o, h, l, c, v
        
    Returns:
        list: รายการข้อมูลในรูปแบบที่เหมาะสม (dict ที่มี keys: timestamp, open, high, low, close)
    """
    result = []
    
    if not raw_data or 't' not in raw_data or not raw_data['t']:
        show_message("ไม่มีข้อมูลที่จะประมวลผล")
        return []
    
    try:
        for i in range(len(raw_data['t'])):
            item = {
                "timestamp": raw_data['t'][i],
                "open": raw_data['o'][i],
                "high": raw_data['h'][i],
                "low": raw_data['l'][i],
                "close": raw_data['c'][i]
            }
            result.append(item)
        
        show_message(f"แปลงข้อมูลสำเร็จ {len(result)} รายการ")
        return result
    except Exception as e:
        show_message(f"เกิดข้อผิดพลาดในการแปลงข้อมูล: {str(e)}")
        return []

# ฟังก์ชันสำหรับการสั่งรันภายนอก
def main():
    """ฟังก์ชันหลักสำหรับการรันจากคำสั่ง"""
    show_message("เริ่มการทำงานของโปรแกรมดึงข้อมูล USD/THB")
    
    # กำหนดช่วงเวลาล่าสุด 3 วัน
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=3)
    
    # แปลงเป็น timestamp
    start_ts = int(start_time.timestamp())
    end_ts = int(end_time.timestamp())
    
    show_message(f"จะดึงข้อมูลตั้งแต่ {start_time} ถึง {end_time}")
    
    # ดึงข้อมูล
    data = get_data_usdthb(start_ts, end_ts)
    
    if data and len(data) > 0:
        show_message(f"ดึงข้อมูลสำเร็จ {len(data)} รายการ")
        for i in range(min(5, len(data))):
            t = datetime.fromtimestamp(data[i]["timestamp"])
            print(f"  {t}: Open={data[i]['open']} High={data[i]['high']} Low={data[i]['low']} Close={data[i]['close']}")
    else:
        show_message("ไม่สามารถดึงข้อมูลได้")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        show_message("ยกเลิกการทำงานโดยผู้ใช้")
    except Exception as e:
        show_message(f"เกิดข้อผิดพลาด: {e}")
    finally:
        show_message("จบการทำงานของโปรแกรม")