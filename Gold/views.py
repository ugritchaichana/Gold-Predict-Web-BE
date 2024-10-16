import pandas as pd
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from .models import Gold_THB, Gold_USD, Gold_CNY
from currency.models import USDTHB, CNYTHB
from datetime import datetime
from django.utils import timezone

class GoldDataUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, format=None):
        file = request.FILES['file']
        gold_currency = request.data.get('gold_currency')

        if gold_currency not in ['usd', 'thb', 'cny']:
            return Response({"error": "Invalid gold currency type."}, status=status.HTTP_400_BAD_REQUEST)

        df = pd.read_csv(file)
        df = df.drop(columns=['ปริมาณ'])
        df.columns = ['Date', 'Price', 'Open', 'High', 'Low', 'Percent']
        df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')
        df['Price'] = pd.to_numeric(df['Price'].str.replace(',', ''), errors='coerce')
        df['Open'] = pd.to_numeric(df['Open'].str.replace(',', ''), errors='coerce')
        df['High'] = pd.to_numeric(df['High'].str.replace(',', ''), errors='coerce')
        df['Low'] = pd.to_numeric(df['Low'].str.replace(',', ''), errors='coerce')
        df['Percent'] = pd.to_numeric(df['Percent'].str.replace('%', ''), errors='coerce')

        full_dates = pd.date_range(start=df['Date'].min(), end=df['Date'].max(), freq='D')
        df = df.set_index('Date').reindex(full_dates).reset_index()
        df.rename(columns={'index': 'Date'}, inplace=True)
        df[['Price', 'Open', 'High', 'Low']] = df[['Price', 'Open', 'High', 'Low']].interpolate(method='linear')
        df['Percent'] = df['Price'].pct_change() * 100
        df['Percent'] = df['Percent'].fillna(0)
        df['Diff'] = df['Price'].diff().fillna(0)

        objects_to_create = []
        if gold_currency.lower() == 'usd':
            for _, row in df.iterrows():
                print(f"✅ Row: {row['Date']} - Price: {row['Price']}")  # แสดงวันที่และราคาที่กำลังประมวลผล

                # พยายามหาข้อมูล usd_thb ในวันที่ตรงกัน
                usd_thb = USDTHB.objects.filter(date=row['Date']).first()

                # ถ้าไม่พบข้อมูลในวันที่ตรงกันให้หาข้อมูลที่ใหม่กว่าวันที่กำลังประมวลผล
                if not usd_thb:
                    usd_thb = USDTHB.objects.filter(date__gte=row['Date']).order_by('date').first()

                # คำนวณราคา THB
                convert_price_th = row['Price'] * usd_thb.price if usd_thb else None  # ใช้ None ถ้าไม่พบข้อมูล

                if usd_thb is None:
                    print(f"No USDTHB data for {row['Date']}")  # ไม่มีข้อมูล USDTHB
                    continue  # ข้ามไปที่แถวถัดไป

                print(f"Creating object: Date={row['Date']}, Price={row['Price']}, Price THB={convert_price_th}")  # แสดงค่าที่จะถูกบันทึก

                objects_to_create.append(Gold_USD(
                    date=row['Date'],
                    price=row['Price'],
                    price_thb=convert_price_th,
                    open=row['Open'],
                    high=row['High'],
                    low=row['Low'],
                    percent=row['Percent'],
                    diff=row['Diff']
                ))
            
            Gold_USD.objects.bulk_create(objects_to_create)
            return Response({"message": "Data uploaded and saved to gold_usd."}, status=status.HTTP_201_CREATED)

        elif gold_currency.lower() == 'cny':
            for _, row in df.iterrows():
                cny_thb = CNYTHB.objects.filter(date=row['Date']).first()
                
                if cny_thb is None:
                    print(f"No CNYTHB data for {row['Date']}")  # ไม่มีข้อมูล CNYTHB
                    continue  # ข้ามไปที่แถวถัดไป
                
                convert_price_th = row['Price'] * cny_thb.price if cny_thb else None
                print(f"✅ Row: {row['Date']} - Price: {row['Price']} - Price THB: {convert_price_th}")  # แสดงวันที่และราคาที่กำลังประมวลผล

                objects_to_create.append(Gold_CNY(
                    date=row['Date'],
                    price=row['Price'],
                    price_thb=convert_price_th,
                    open=row['Open'],
                    high=row['High'],
                    low=row['Low'],
                    percent=row['Percent'],
                    diff=row['Diff']
                ))

            Gold_CNY.objects.bulk_create(objects_to_create)
            print(f"Successfully uploaded {len(objects_to_create)} CNY records.")
            return Response({"message": "Data uploaded and saved to gold_cny successfully."}, status=status.HTTP_201_CREATED)

        elif gold_currency.lower() == 'thb':
            for _, row in df.iterrows():
                print(f"✅ Row: {row['Date']} - Price: {row['Price']}")  # แสดงวันที่และราคาที่กำลังประมวลผล

                objects_to_create.append(Gold_THB(
                    date=row['Date'],
                    price=row['Price'],
                    open=row['Open'],
                    high=row['High'],
                    low=row['Low'],
                    percent=row['Percent'],
                    diff=row['Diff']
                ))
            
            Gold_THB.objects.bulk_create(objects_to_create)
            print(f"Successfully uploaded {len(objects_to_create)} THB records.")
            return Response({"message": "Data uploaded and saved to gold_thb successfully."}, status=status.HTTP_201_CREATED)

        return Response({"error": "Invalid gold currency type."}, status=status.HTTP_400_BAD_REQUEST)


class GoldDataDeleteView(APIView):
    def delete(self, request, format=None):
        gold_currency = request.query_params.get('gold_currency')

        if gold_currency == 'usd':
            Gold_USD.objects.all().delete()
            return Response({"message": "All records from Gold_USD deleted successfully."}, status=status.HTTP_200_OK)

        elif gold_currency == 'thb':
            Gold_THB.objects.all().delete()
            return Response({"message": "All records from Gold_THB deleted successfully."}, status=status.HTTP_200_OK)

        elif gold_currency == 'cny':
            Gold_CNY.objects.all().delete()
            return Response({"message": "All records from Gold_CNY deleted successfully."}, status=status.HTTP_200_OK)

        return Response({"error": "Invalid gold currency type."}, status=status.HTTP_400_BAD_REQUEST)


class GoldDataListView(APIView):
    def get(self, request, format=None):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        gold_currency = request.query_params.get('gold_currency', None)

        # กำหนดค่า default สำหรับ start_date และ end_date
        if start_date:
            start_date = timezone.make_aware(datetime.strptime(start_date, '%Y-%m-%d'))
        if end_date:
            end_date = timezone.make_aware(datetime.strptime(end_date, '%Y-%m-%d'))
        else:
            end_date = timezone.now()  # ใช้วันที่ปัจจุบันถ้าไม่ได้ระบุ end_date

        # กำหนด queryset ตาม gold_currency ที่เลือก
        if gold_currency == 'usd':
            data = Gold_USD.objects.filter(date__range=(start_date, end_date))
        elif gold_currency == 'thb':
            data = Gold_THB.objects.filter(date__range=(start_date, end_date))
        elif gold_currency == 'cny':
            data = Gold_CNY.objects.filter(date__range=(start_date, end_date))
        else:
            # ถ้าไม่ได้ระบุ gold_currency จะแสดงข้อมูลทั้งหมดจากทุก table
            data_usd = Gold_USD.objects.filter(date__range=(start_date, end_date))
            data_thb = Gold_THB.objects.filter(date__range=(start_date, end_date))
            data_cny = Gold_CNY.objects.filter(date__range=(start_date, end_date))
            data = {
                'usd': list(data_usd.values()),
                'thb': list(data_thb.values()),
                'cny': list(data_cny.values()),
            }
            return Response(data, status=status.HTTP_200_OK)

        # ส่งข้อมูลในรูปแบบ JSON
        return Response(list(data.values()), status=status.HTTP_200_OK)
    
class GoldDataDeleteByIdView(APIView):
    def delete(self, request, format=None):
        gold_currency = request.query_params.get('gold_currency')
        id = request.query_params.get('id')

        if not id or not gold_currency:
            return Response({"error": "Both id and gold_currency are required."}, status=status.HTTP_400_BAD_REQUEST)

        if gold_currency == 'usd':
            try:
                record = Gold_USD.objects.get(id=id)
                record.delete()
                return Response({"message": f"Record with id {id} from Gold_USD deleted successfully."}, status=status.HTTP_200_OK)
            except Gold_USD.DoesNotExist:
                return Response({"error": f"Record with id {id} not found in Gold_USD."}, status=status.HTTP_404_NOT_FOUND)

        elif gold_currency == 'thb':
            try:
                record = Gold_THB.objects.get(id=id)
                record.delete()
                return Response({"message": f"Record with id {id} from Gold_THB deleted successfully."}, status=status.HTTP_200_OK)
            except Gold_THB.DoesNotExist:
                return Response({"error": f"Record with id {id} not found in Gold_THB."}, status=status.HTTP_404_NOT_FOUND)

        elif gold_currency == 'cny':
            try:
                record = Gold_CNY.objects.get(id=id)
                record.delete()
                return Response({"message": f"Record with id {id} from Gold_CNY deleted successfully."}, status=status.HTTP_200_OK)
            except Gold_CNY.DoesNotExist:
                return Response({"error": f"Record with id {id} not found in Gold_CNY."}, status=status.HTTP_404_NOT_FOUND)

        return Response({"error": "Invalid gold currency type."}, status=status.HTTP_400_BAD_REQUEST)
