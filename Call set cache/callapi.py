import requests
import datetime

def call_api():
    url = "https://api.coindesk.com/v1/bpi/currentprice.json"  # ตัวอย่าง API
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # ถ้ามี error จะ throw exception
        data = response.json()

        # ตัวอย่าง: บันทึกข้อมูลและเวลาไว้ในไฟล์
        with open("/home/username/scripts/api_log.txt", "a") as f:
            f.write(f"[{datetime.datetime.now()}] Response:\n")
            f.write(str(data) + "\n\n")

    except requests.RequestException as e:
        with open("/home/username/scripts/api_log.txt", "a") as f:
            f.write(f"[{datetime.datetime.now()}] ERROR: {e}\n\n")

if __name__ == "__main__":
    call_api()