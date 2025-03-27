import requests
from xml.etree import ElementTree as ET
import time

# ฟังก์ชันสำหรับดึงข้อมูล sitemap
def fetch_sitemap(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

# ฟังก์ชันสำหรับค้นหา URL ที่เกี่ยวข้องกับทองคำ
def find_gold_related_urls(sitemap_xml):
    gold_urls = []
    root = ET.fromstring(sitemap_xml)
    
    # ค้นหาทั้งใน sitemap หลักและ child sitemap
    for elem in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
        url = elem.text
        if "gold" in url.lower():
            gold_urls.append(url)
    
    return gold_urls

# ดึง Sitemap Index
sitemap_index_url = "https://www.finnomena.com/sitemap_index.xml"
index_content = fetch_sitemap(sitemap_index_url)

if index_content:
    root = ET.fromstring(index_content)
    all_sitemaps = []
    gold_related_sitemaps = []
    
    # ดึงทุก sitemap URL จาก index
    for sitemap in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap"):
        loc = sitemap.find(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc").text
        all_sitemaps.append(loc)
    
    # ตรวจสอบแต่ละ sitemap ว่ามีข้อมูลทองคำหรือไม่
    for sitemap_url in all_sitemaps:
        print(f"Processing: {sitemap_url}")
        sitemap_content = fetch_sitemap(sitemap_url)
        if sitemap_content:
            gold_urls = find_gold_related_urls(sitemap_content)
            if gold_urls:
                gold_related_sitemaps.extend(gold_urls)
        time.sleep(2)  # พัก 2 วินาทีเพื่อป้องกันการถูกบล็อก
    
    # แสดงผลลัพธ์
    print("\nGold-related URLs found:")
    for url in gold_related_sitemaps:
        print(f"- {url}")

else:
    print("Failed to retrieve sitemap index")