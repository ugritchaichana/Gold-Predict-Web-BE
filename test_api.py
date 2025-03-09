import requests

base_url = "http://localhost:8000/finnomenaGold/get-gold-data/"

def test_api(params, expected_status, expected_message=None):
    response = requests.get(base_url, params=params)
    result = {
        "params": params,
        "status_code": response.status_code,
        "response": response.json()
    }
    if response.status_code != expected_status:
        result["error"] = f"Expected status {expected_status}, got {response.status_code}"
    if expected_message and expected_message not in response.text:
        result["error"] = f"Expected message '{expected_message}', got {response.text}"
    return result

# ทดสอบการเรียก API โดยไม่มีพารามิเตอร์ db_choice
results = []
results.append(test_api({}, 400, "Missing 'db_choice' parameter."))

# ทดสอบการเรียก API โดยใช้ db_choice ที่ไม่ถูกต้อง
results.append(test_api({"db_choice": "2"}, 400, "Invalid 'db_choice' parameter value. Must be 0 or 1."))

# ทดสอบการเรียก API โดยใช้ db_choice ที่ถูกต้อง แต่ไม่มีพารามิเตอร์ frame, start, end
results.append(test_api({"db_choice": "0"}, 200))

# ทดสอบการเรียก API โดยใช้ frame ที่ไม่ถูกต้อง
results.append(test_api({"db_choice": "0", "frame": "invalid"}, 400, "Invalid 'frame' parameter."))

# ทดสอบการเรียก API โดยใช้ start และ end ที่ไม่อยู่ในรูปแบบ dd-mm-yyyy
results.append(test_api({"db_choice": "0", "start": "2023-01-01", "end": "2023-01-10"}, 400, "Invalid date format. Use 'dd-mm-yyyy'."))

# ทดสอบการเรียก API โดยใช้ start ที่มากกว่า end
results.append(test_api({"db_choice": "0", "start": "10-01-2023", "end": "01-01-2023"}, 400, "'start' date cannot be after 'end' date."))

# ทดสอบการเรียก API โดยใช้ frame เป็น 1d และไม่มีข้อมูลของวันนี้
results.append(test_api({"db_choice": "0", "frame": "1d"}, 200))

# ทดสอบการเรียก API โดยใช้ frame เป็น 1d และมีข้อมูลของวันนี้
# (ต้องมีข้อมูลของวันนี้ในฐานข้อมูล)
results.append(test_api({"db_choice": "0", "frame": "1d"}, 200))

# ทดสอบการเรียก API โดยใช้ frame เป็น 7d, 15d, 1m, 3m, 6m, 1y, 3y, all
frames = ["7d", "15d", "1m", "3m", "6m", "1y", "3y", "all"]
for frame in frames:
    results.append(test_api({"db_choice": "0", "frame": frame}, 200))

# ทดสอบการเรียก API โดยใช้ group_by เป็น daily และ monthly
group_bys = ["daily", "monthly"]
for group_by in group_bys:
    results.append(test_api({"db_choice": "0", "group_by": group_by}, 200))

# ทดสอบการเรียก API โดยใช้แคช (cache=True และ cache=False)
results.append(test_api({"db_choice": "0", "cache": "True"}, 200))
results.append(test_api({"db_choice": "0", "cache": "False"}, 200))

# บันทึกผลการทดสอบลงในไฟล์
with open("test_results.txt", "w") as f:
    for result in results:
        f.write(f"Params: {result['params']}\n")
        f.write(f"Status Code: {result['status_code']}\n")
        f.write(f"Response: {result['response']}\n")
        if "error" in result:
            f.write(f"Error: {result['error']}\n")
        f.write("-" * 80 + "\n")
