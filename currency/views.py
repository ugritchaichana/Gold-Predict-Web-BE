import pandas as pd
import os
from django.db.models import Avg, Min, Max
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from .models import USDTHB, CNYTHB
from .serializers import USDTHBSerializer, CNYTHBSerializer
from datetime import datetime, timedelta
from datetime import date as DateType
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
import json
from django.http import JsonResponse
from django.core.cache import cache
import logging
logger = logging.getLogger(__name__)


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
    logger = logging.getLogger(__name__)

    def post(self, request, format=None):
        self.logger.info("Received a POST request to upload currency data.")
        
        try:
            file = request.FILES['file']
            currency = request.data.get('currency')
            self.logger.info(f"File received: {file.name}, Currency: {currency}")

            if currency not in ['usd', 'cny']:
                self.logger.error("Invalid currency type received.")
                return Response({"error": "Invalid currency type."}, status=status.HTTP_400_BAD_REQUEST)

            df = pd.read_csv(file)
            self.logger.info("CSV file read successfully.")
            self.logger.info(f"Data preview:\n{df.head()}")  # Display the first few rows of the dataframe

            df = df.drop(columns=['ปริมาณ'], errors='ignore')
            df.columns = ['Date', 'Price', 'Open', 'High', 'Low', 'Percent']
            self.logger.info("Data columns renamed and unnecessary columns dropped.")

            df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')
            df['Percent'] = pd.to_numeric(df['Percent'].str.replace('%', '', regex=True), errors='coerce')
            self.logger.info("Date and Percent columns processed.")

            full_dates = pd.date_range(start=df['Date'].min(), end=df['Date'].max(), freq='D')
            df = df.set_index('Date').reindex(full_dates).reset_index()
            df.rename(columns={'index': 'Date'}, inplace=True)
            self.logger.info("Missing dates filled.")

            df[['Price', 'Open', 'High', 'Low']] = df[['Price', 'Open', 'High', 'Low']].interpolate(method='linear')
            df['Percent'] = df['Price'].pct_change() * 100
            df['Percent'] = df['Percent'].fillna(0)
            df['Diff'] = df['Price'].diff().fillna(0)
            self.logger.info("Data interpolation and calculations completed.")

            df = df.round({'Price': 4, 'Open': 4, 'High': 4, 'Low': 4, 'Percent': 4, 'Diff': 4})
            self.logger.info("Data rounded to 4 decimal places.")

            objects_to_create = []
            model = USDTHB if currency.lower() == 'usd' else CNYTHB

            for _, row in df.iterrows():
                objects_to_create.append(model(
                    date=row['Date'],
                    price=row['Price'],
                    open=row['Open'],
                    high=row['High'],
                    low=row['Low'],
                    percent=row['Percent'],
                    diff=row['Diff']
                ))

            model.objects.bulk_create(objects_to_create)
            self.logger.info(f"Data uploaded and saved to {model.__name__.lower()} successfully.")

            return Response({"message": f"Data uploaded and saved to {model.__name__.lower()} successfully."},
                            status=status.HTTP_201_CREATED)
        except Exception as e:
            self.logger.error(f"An error occurred: {str(e)}")
            return Response({"error": "An error occurred during the upload process."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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


def serialize_data(data):
    for entry in data:
        if "date" in entry and isinstance(entry["date"], DateType):
            entry["date"] = entry["date"].isoformat()
    return data

def apply_max(data, max_val):
    """
    Apply max parameter to limit the number of data points while ensuring first and last points are included.
    Data points between first and last are distributed evenly.
    """
    if max_val and len(data) > int(max_val):
        max_val = int(max_val)
        
        # If max_val is less than 2, return at least first point
        if max_val < 2:
            return [data[0]]
            
        # Always include first and last points
        selected = [data[0]]
        
        # If we have more than 2 points to select, distribute the middle ones evenly
        if max_val > 2:
            # Calculate step size for the middle points (excluding first and last)
            step = (len(data) - 1) / (max_val - 1)
            
            # Add the middle points (excluding first which was already added and last which will be added)
            for i in range(1, max_val - 1):
                idx = int(i * step)
                selected.append(data[idx])
        
        # Add the last point
        selected.append(data[-1])
        
        return selected
    return data

def get_currency_data(request):
    frame = request.GET.get('frame', None)
    start_date = request.GET.get('start', None)
    end_date = request.GET.get('end', None)
    group_by = request.GET.get('group_by', 'daily')
    max_points = request.GET.get('max')  # Add max parameter support

    cache_time = 3600  # Cache time in seconds (1 hour)
    use_cache = request.GET.get('cache', 'True').lower() != 'false'

    try:
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        if start_date and end_date and start_date > end_date:
            return JsonResponse({"error": "'start' date cannot be after 'end' date."}, status=400)
    except ValueError:
        return JsonResponse({"error": "Invalid date format. Use 'YYYY-MM-DD'."}, status=400)

    end_timeframe = datetime.now().date()
    if not start_date:
        start_date = end_timeframe

    if frame:
        if frame == "1d":
            start_date = end_timeframe
        elif frame == "7d":
            start_date = end_timeframe - timedelta(days=6)
        elif frame == "15d":
            start_date = end_timeframe - timedelta(days=14)
        elif frame == "1m":
            # Fix: Show last 30 days instead of just current month
            start_date = end_timeframe - timedelta(days=30)
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
        
    # Cache key - include max_points in cache key
    cache_key = f"currency_data:{start_date}:{end_date}:{frame}:{group_by}:{max_points}"
    logger.info(f"Generated cache key: {cache_key}")

    # Check Cache first
    cache_status = "None"
    cache_used = "PostgreSQL"
    if use_cache:
        cached_data = cache.get(cache_key)
        if cached_data:
            try:
                cached_data = json.loads(cached_data)
                logger.info(f"Cache hit: Using cached data for key: {cache_key}")
                cache_status = cache_key
                cache_used = "redis"  # If cache is used, set to "redis"
                # Return result from Redis with consistent fields
                return JsonResponse({
                    "cache_used": cache_used,
                    "cache": cache_status,
                    "count": len(cached_data["data"]),
                    "data": cached_data["data"]
                }, status=200)
            except json.JSONDecodeError:
                logger.warning(f"Cache data corrupted for key: {cache_key}, ignoring cache.")

    queryset = USDTHB.objects.all()

    if start_date:
        queryset = queryset.filter(date__gte=start_date)
    if end_date:
        queryset = queryset.filter(date__lte=end_date)

    if frame == "1d" and not queryset.exists():
        latest_entry = USDTHB.objects.order_by('-date').first()
        if latest_entry:
            queryset = USDTHB.objects.filter(date=latest_entry.date)

    if group_by == "daily":
        queryset = queryset.order_by('date')
        data = list(queryset.values())
        
        # Apply max parameter to limit data points if provided
        if max_points:
            data = apply_max(data, max_points)

    elif group_by == "monthly":
        queryset = queryset.values("date__year", "date__month").annotate(
            avg_price=Avg("price"),
            avg_open=Avg("open"),
            avg_high=Avg("high"),
            avg_low=Avg("low"),
            avg_percent=Avg("percent"),
            avg_diff=Avg("diff"),
            min_price=Min("price"),
            max_price=Max("price"),
        ).order_by("date__year", "date__month")

        data = [
            {
                "period": f"{entry['date__year']}-{entry['date__month']:02d}",
                "avg_price": entry["avg_price"],
                "avg_open": entry["avg_open"],
                "avg_high": entry["avg_high"],
                "avg_low": entry["avg_low"],
                "avg_percent": entry["avg_percent"],
                "avg_diff": entry["avg_diff"],
                "min_price": entry["min_price"],
                "max_price": entry["max_price"],
            }
            for entry in queryset
        ]
        
        # Apply max parameter to limit data points if provided
        if max_points:
            data = apply_max(data, max_points)

    else:
        return JsonResponse({"error": "Invalid 'group_by' parameter. Use 'daily' or 'monthly'."}, status=400)

    # Store the result in cache
    if use_cache:
        # แปลง Python Object เป็น JSON String ก่อนเก็บเข้า Redis
        cache.set(cache_key, json.dumps({"data": serialize_data(data)}), timeout=cache_time)
        logger.info(f"Cached data for key: {cache_key}")
        cache_status = cache_key  # Set cache key after caching data

    # Return response with the cache source
    return JsonResponse({
        "cache_used": cache_used,
        "cache": cache_status,
        "count": len(data),
        "data": serialize_data(data)
    })
