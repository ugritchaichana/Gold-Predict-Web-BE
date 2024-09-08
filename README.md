ติดตั้ง
1. เข้า CMD ใช้คำสั่ง >> .venv\Scripts\activate <<
2. เข้า CMD ใช้คำสั่ง >> pip install -r requirements.txt <<
3. ใช้งาน >> py Backend/manage.py runserver <<


สร้าง App
- >> django-admin startapp { ชื่อ App } <<
- ตัวอย่าง django-admin startapp boothapp
- เพิ่มชื่อ App ที่ไฟล์ Backend\Backend\settings.py ที่ Array -> INSTALLED_APPS
- เพิ่มเส้น Route ที่ไฟล์ Backend\Backend\urls.py ที่ Array -> urlpatterns





---------------- เพิ่มเติม ----------------

ใช้ .venv
- ใช้ CMD
- พิมพ์ .venv\Scripts\activate
- ( " ชื่อ ENV "\Scripts\activate )
- ถ้าใช้แล้วจะมีชื่อ venv ขึ้นที่หน้าตัวหนังสือใน cmd ตัวอย่าง >> (.venv) C:\Users\ugrit\Gold-Predict-Web-BE> <<
- ออกจาก VENV พิมพ์ deactivate 


ติดตั้ง package จาก requirements.txt
- พิมพ์ pip install -r requirements.txt


pip freeze > requirements.txt



สร้าง .venv
- เข้าเมนูค้นหาไฟล์ของ vscode (อยู่ด้านบนกลาง)
- เข้าที่ >Python: Create Environment...

---------------- เพิ่มเติม ----------------
