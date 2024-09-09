# การติดตั้งและการใช้งาน

## การติดตั้ง

1. เปิด CMD แล้วใช้คำสั่งเพื่อเปิดใช้งาน virtual environment:
    ```bash
    .venv\Scripts\activate
    ```
2. ติดตั้ง dependencies จากไฟล์ `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```
3. รันเซิร์ฟเวอร์ Django:
    ```bash
    py Backend/manage.py runserver
    ```

## การสร้างแอป (App)

1. สร้างแอปใหม่:
    ```bash
    django-admin startapp {ชื่อแอป}
    ```
   ตัวอย่าง: 
    ```bash
    django-admin startapp boothapp
    ```

2. เพิ่มชื่อแอปในไฟล์ `Backend\Backend\settings.py` ที่ตัวแปร `INSTALLED_APPS`

3. เพิ่มเส้นทาง (Route) ในไฟล์ `Backend\Backend\urls.py` ที่ตัวแปร `urlpatterns`

---

# คำแนะนำเพิ่มเติม

## การใช้ .venv

1. เปิด CMD แล้วพิมพ์คำสั่งเพื่อเปิดใช้งาน virtual environment:
    ```bash
    .venv\Scripts\activate
    ```

2. หากใช้งานถูกต้องจะมีชื่อ virtual environment ปรากฏใน command prompt เช่น:
    ```
    (.venv) C:\Users\ugrit\Gold-Predict-Web-BE>
    ```

3. เมื่อต้องการออกจาก virtual environment:
    ```bash
    deactivate
    ```

## การติดตั้งแพ็กเกจจาก `requirements.txt`

ติดตั้งแพ็กเกจทั้งหมดที่ระบุในไฟล์ `requirements.txt`:
```bash
pip install -r requirements.txt
