import pandas as pd
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from .models import USDTHB, CNYTHB
from .serializers import USDTHBSerializer, CNYTHBSerializer
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse

class CurrencyDataCreateView(APIView):
    def post(self, request, format=None):
        # รับข้อมูลจาก request
        data = request.data
        currency = data.get('currency')
        date = data.get('date')
        price = data.get('price')
        open_price = data.get('open')
        high = data.get('high')
        low = data.get('low')
        percent = data.get('percent')
        diff = data.get('diff')

        # ตรวจสอบข้อมูล currency
        if currency not in ['usd', 'cny']:
            return Response({"error": "Invalid currency type."}, status=status.HTTP_400_BAD_REQUEST)

        # ตรวจสอบว่าข้อมูลวันที่มีอยู่หรือไม่
        try:
            date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        # ตรวจสอบประเภทของ currency และบันทึกลงใน database
        if currency.lower() == 'usd':
            # เพิ่มข้อมูลในตาราง USDTHB
            usd_record = USDTHB(
                date=date,
                price=price,
                open=open_price,
                high=high,
                low=low,
                percent=percent,
                diff=diff
            )
            usd_record.save()
            return Response({"message": "Data added to USDTHB successfully."}, status=status.HTTP_201_CREATED)

        elif currency.lower() == 'cny':
            # เพิ่มข้อมูลในตาราง CNYTHB
            cny_record = CNYTHB(
                date=date,
                price=price,
                open=open_price,
                high=high,
                low=low,
                percent=percent,
                diff=diff
            )
            cny_record.save()
            return Response({"message": "Data added to CNYTHB successfully."}, status=status.HTTP_201_CREATED)

        return Response({"error": "Invalid currency type."}, status=status.HTTP_400_BAD_REQUEST)

class CurrencyDataUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, format=None):
        file = request.FILES['file']
        currency = request.data.get('currency')

        if currency not in ['usd', 'cny']:
            return Response({"error": "Invalid currency type."}, status=status.HTTP_400_BAD_REQUEST)

        df = pd.read_csv(file)
        df = df.drop(columns=['ปริมาณ'])
        df.columns = ['Date', 'Price', 'Open', 'High', 'Low', 'Percent']
        df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')
        df['Percent'] = pd.to_numeric(df['Percent'].str.replace('%', ''), errors='coerce')

        full_dates = pd.date_range(start=df['Date'].min(), end=df['Date'].max(), freq='D')
        df = df.set_index('Date').reindex(full_dates).reset_index()
        df.rename(columns={'index': 'Date'}, inplace=True)

        df[['Price', 'Open', 'High', 'Low']] = df[['Price', 'Open', 'High', 'Low']].interpolate(method='linear')
        df['Percent'] = df['Price'].pct_change() * 100
        df['Percent'] = df['Percent'].fillna(0)
        df['Diff'] = df['Price'].diff().fillna(0)

        df['Price'] = df['Price'].round(4)
        df['Open'] = df['Open'].round(4)
        df['High'] = df['High'].round(4)
        df['Low'] = df['Low'].round(4)
        df['Percent'] = df['Percent'].round(4)
        df['Diff'] = df['Diff'].round(4)

        output_folder = f'cleaned-files/{currency}'
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        current_time = datetime.now().strftime("%d%m%y_%H%M")
        file_name = f"{currency.lower()}-{current_time}.csv"
        file_path = os.path.join(output_folder, file_name)

        df.to_csv(file_path, index=False)

        objects_to_create = []
        if currency.lower() == 'usd':
            for _, row in df.iterrows():
                objects_to_create.append(USDTHB(
                    date=row['Date'],
                    price=row['Price'],
                    open=row['Open'],
                    high=row['High'],
                    low=row['Low'],
                    percent=row['Percent'],
                    diff=row['Diff']
                ))
            USDTHB.objects.bulk_create(objects_to_create)
            return Response({"message": f"Data uploaded and saved to usdthb successfully. File saved as {file_name}"}, status=status.HTTP_201_CREATED)

        elif currency.lower() == 'cny':
            for _, row in df.iterrows():
                objects_to_create.append(CNYTHB(
                    date=row['Date'],
                    price=row['Price'],
                    open=row['Open'],
                    high=row['High'],
                    low=row['Low'],
                    percent=row['Percent'],
                    diff=row['Diff']
                ))
            CNYTHB.objects.bulk_create(objects_to_create)
            return Response({"message": f"Data uploaded and saved to cnythb successfully. File saved as {file_name}"}, status=status.HTTP_201_CREATED)

        return Response({"error": "Invalid currency type."}, status=status.HTTP_400_BAD_REQUEST)

# class CurrencyDataListView(APIView):

#     def get(self, request, format=None):
#         start_date = request.query_params.get('start_date')
#         end_date = request.query_params.get('end_date')
#         currency = request.query_params.get('currency')

#         if currency:
#             if currency.lower() == 'usd':
#                 model = USDTHB
#             elif currency.lower() == 'cny':
#                 model = CNYTHB
#             else:
#                 return Response({"error": "Invalid currency type."}, status=status.HTTP_400_BAD_REQUEST)

#             if start_date and end_date:
#                 data = model.objects.filter(date__range=[start_date, end_date]).order_by('date')
#             else:
#                 data = model.objects.all().order_by('date')

#             if currency.lower() == 'usd':
#                 serializer = USDTHBSerializer(data, many=True)
#             else:
#                 serializer = CNYTHBSerializer(data, many=True)

#             return Response(serializer.data, status=status.HTTP_200_OK)

#         return Response({"error": "Currency not specified."}, status=status.HTTP_400_BAD_REQUEST)

class CurrencyDataDeleteView(APIView):

    def delete(self, request, format=None):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        currency = request.query_params.get('currency')

        if currency:
            if currency.lower() == 'usd':
                model = USDTHB
            elif currency.lower() == 'cny':
                model = CNYTHB
            else:
                return Response({"error": "Invalid currency type."}, status=status.HTTP_400_BAD_REQUEST)

            if start_date and end_date:
                deleted_count, _ = model.objects.filter(date__range=[start_date, end_date]).delete()
                return Response({
                    "message": f"Deleted {deleted_count} records for {currency.upper()}."
                }, status=status.HTTP_204_NO_CONTENT)
            else:
                deleted_count, _ = model.objects.all().delete()
                return Response({
                    "message": f"Deleted all records for {currency.upper()}."
                }, status=status.HTTP_204_NO_CONTENT)

        return Response({"error": "Currency not specified."}, status=status.HTTP_400_BAD_REQUEST)

class CurrencyDataDeleteByIdView(APIView):

    def delete(self, request, format=None):
        record_id = request.query_params.get('id')
        currency = request.query_params.get('currency')

        if not record_id:
            return Response({"error": "ID not specified."}, status=status.HTTP_400_BAD_REQUEST)

        if currency:
            if currency.lower() == 'usd':
                model = USDTHB
            elif currency.lower() == 'cny':
                model = CNYTHB
            else:
                return Response({"error": "Invalid currency type."}, status=status.HTTP_400_BAD_REQUEST)

            try:
                instance = model.objects.get(id=record_id)
                instance.delete()
                return Response({
                    "message": f"Deleted record with ID {record_id} for {currency.upper()}."
                }, status=status.HTTP_204_NO_CONTENT)
            except model.DoesNotExist:
                return Response({"error": "Record not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response({"error": "Currency not specified."}, status=status.HTTP_400_BAD_REQUEST)


from django.db.models import Q
from datetime import datetime, timedelta
def get_currency_data(request):
    # Get frame and date range parameters
    frame = request.GET.get('frame', None)  # 1d, 7d, 15d, 1m, 3m, 1y, 3y, all
    start_date = request.GET.get('start', None)
    end_date = request.GET.get('end', None)

    # Validate and parse start and end date
    try:
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        if start_date and end_date and start_date > end_date:
            return JsonResponse({"error": "'start' date cannot be after 'end' date."}, status=400)
    except ValueError:
        return JsonResponse({"error": "Invalid date format. Use 'YYYY-MM-DD'."}, status=400)

    # Prepare date filter based on frame
    end_timeframe = datetime.now().date()
    if not start_date:
        start_date = end_timeframe

    # Handle frame logic
    if frame:
        if frame == "1d":
            start_date = end_timeframe
        elif frame == "7d":
            start_date = end_timeframe - timedelta(days=6)
        elif frame == "15d":
            start_date = end_timeframe - timedelta(days=14)
        elif frame == "1m":
            start_date = end_timeframe.replace(day=1)  # The first day of the current month
        elif frame == "3m":
            start_date = end_timeframe - timedelta(days=90)
        elif frame == "1y":
            start_date = end_timeframe.replace(year=end_timeframe.year - 1)
        elif frame == "3y":
            start_date = end_timeframe.replace(year=end_timeframe.year - 3)
        elif frame == "all":
            start_date = None
        else:
            return JsonResponse({"error": "Invalid 'frame' parameter."}, status=400)

    # Query USDTHB data based on start and end date
    queryset = USDTHB.objects.all()

    if start_date:
        queryset = queryset.filter(date__gte=start_date)
    if end_date:
        queryset = queryset.filter(date__lte=end_date)

    # Handle the case for '1d' frame where no data exists and fallback to latest date
    if frame == "1d" and not queryset.exists():
        latest_entry = USDTHB.objects.order_by('-date').first()
        if latest_entry:
            queryset = USDTHB.objects.filter(date=latest_entry.date)

    # Order the data by id in ascending order
    queryset = queryset.order_by('id')

    # Prepare the response data
    data = list(queryset.values())

    return JsonResponse({"data": data, "count": len(data)})

@csrf_exempt
def add_usdthb_data(request):
    if request.method == 'POST':
        try:
            # รับข้อมูล JSON จาก request
            data = json.loads(request.body)

            # ตรวจสอบว่า keys ของข้อมูลครบถ้วนหรือไม่
            date = data.get('date')
            price = data.get('price', None)
            open_value = data.get('open', None)
            high = data.get('high', None)
            low = data.get('low', None)
            percent = data.get('percent', None)
            diff = data.get('diff', None)

            # สร้าง record ใหม่
            usdthb_record = USDTHB.objects.create(
                date=date,
                price=price,
                open=open_value,
                high=high,
                low=low,
                percent=percent,
                diff=diff
            )

            return JsonResponse({"message": "Data added successfully", "data": data}, status=201)
        
        except Exception as e:
            return JsonResponse({"message": str(e)}, status=400)

    return JsonResponse({"message": "Only POST method is allowed"}, status=405)