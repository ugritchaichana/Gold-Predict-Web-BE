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

    def post(self, request, format=None):
        file = request.FILES['file']
        currency = request.data.get('currency')

        if currency not in ['usd', 'cny']:
            return Response({"error": "Invalid currency type."}, status=status.HTTP_400_BAD_REQUEST)

        df = pd.read_csv(file)
        df = df.drop(columns=['ปริมาณ'], errors='ignore')
        df.columns = ['Date', 'Price', 'Open', 'High', 'Low', 'Percent']
        
        df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')
        df['Percent'] = pd.to_numeric(df['Percent'].str.replace('%', '', regex=True), errors='coerce')

        full_dates = pd.date_range(start=df['Date'].min(), end=df['Date'].max(), freq='D')
        df = df.set_index('Date').reindex(full_dates).reset_index()
        df.rename(columns={'index': 'Date'}, inplace=True)

        df[['Price', 'Open', 'High', 'Low']] = df[['Price', 'Open', 'High', 'Low']].interpolate(method='linear')
        df['Percent'] = df['Price'].pct_change() * 100
        df['Percent'] = df['Percent'].fillna(0)
        df['Diff'] = df['Price'].diff().fillna(0)

        df = df.round({'Price': 4, 'Open': 4, 'High': 4, 'Low': 4, 'Percent': 4, 'Diff': 4})

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

        return Response({"message": f"Data uploaded and saved to {model.__name__.lower()} successfully."},
                        status=status.HTTP_201_CREATED)

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


def get_currency_data(request):
    frame = request.GET.get('frame', None)
    start_date = request.GET.get('start', None)
    end_date = request.GET.get('end', None)
    group_by = request.GET.get('group_by', 'daily')

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
            start_date = end_timeframe.replace(day=1)
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

    # Cache key
    cache_key = f"currency_data:{start_date}:{end_date}:{frame}:{group_by}"
    logger.info(f"Generated cache key: {cache_key}")

    # Check Cache first
    cache_status = "None"  # Default status when no cache is hit
    if use_cache:
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.info(f"Using cached data for key: {cache_key}")
            cache_status = cache_key  # Cache hit, use the key
            return JsonResponse({"data": cached_data["data"], "count": len(cached_data["data"]), "cache": cache_status}, status=200)
        else:
            logger.info(f"Cache miss for key: {cache_key}")
    
    # If cache miss, proceed with querying the database
    queryset = USDTHB.objects.all()

    if start_date:
        queryset = queryset.filter(date__gte=start_date)
    if end_date:
        queryset = queryset.filter(date__lte=end_date)

    if frame == "1d" and not queryset.exists():
        latest_entry = USDTHB.objects.order_by('-date').first()
        if latest_entry:
            queryset = USDTHB.objects.filter(date=latest_entry.date)

    # Grouping Logic
    if group_by == "daily":
        queryset = queryset.order_by('date')
        data = list(queryset.values())

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

    else:
        return JsonResponse({"error": "Invalid 'group_by' parameter. Use 'daily' or 'monthly'."}, status=400)

    # Store the result in cache if not using cache or cache miss
    if use_cache:
        cache.set(cache_key, {"data": data}, timeout=cache_time)
        logger.info(f"Cached data for key: {cache_key}")
        cache_status = cache_key  # Set cache key after caching data

    return JsonResponse({"data": data, "count": len(data), "cache": cache_status})




# def get_currency_data(request):
#     frame = request.GET.get('frame', None)
#     start_date = request.GET.get('start', None)
#     end_date = request.GET.get('end', None)
#     group_by = request.GET.get('group_by', 'daily')

#     try:
#         if start_date:
#             start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
#         if end_date:
#             end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
#         if start_date and end_date and start_date > end_date:
#             return JsonResponse({"error": "'start' date cannot be after 'end' date."}, status=400)
#     except ValueError:
#         return JsonResponse({"error": "Invalid date format. Use 'YYYY-MM-DD'."}, status=400)

#     end_timeframe = datetime.now().date()
#     if not start_date:
#         start_date = end_timeframe

#     if frame:
#         if frame == "1d":
#             start_date = end_timeframe
#         elif frame == "7d":
#             start_date = end_timeframe - timedelta(days=6)
#         elif frame == "15d":
#             start_date = end_timeframe - timedelta(days=14)
#         elif frame == "1m":
#             start_date = end_timeframe.replace(day=1)
#         elif frame == "3m":
#             start_date = end_timeframe - timedelta(days=90)
#         elif frame == "1y":
#             start_date = end_timeframe.replace(year=end_timeframe.year - 1)
#         elif frame == "3y":
#             start_date = end_timeframe.replace(year=end_timeframe.year - 3)
#         elif frame == "all":
#             start_date = None
#         else:
#             return JsonResponse({"error": "Invalid 'frame' parameter."}, status=400)

#     queryset = USDTHB.objects.all()

#     if start_date:
#         queryset = queryset.filter(date__gte=start_date)
#     if end_date:
#         queryset = queryset.filter(date__lte=end_date)

#     if frame == "1d" and not queryset.exists():
#         latest_entry = USDTHB.objects.order_by('-date').first()
#         if latest_entry:
#             queryset = USDTHB.objects.filter(date=latest_entry.date)

#     # 🟢 Grouping Logic
#     if group_by == "daily":
#         queryset = queryset.order_by('date')
#         data = list(queryset.values())

#     elif group_by == "monthly":
#         queryset = queryset.values("date__year", "date__month").annotate(
#             avg_price=Avg("price"),
#             avg_open=Avg("open"),
#             avg_high=Avg("high"),
#             avg_low=Avg("low"),
#             avg_percent=Avg("percent"),
#             avg_diff=Avg("diff"),
#             min_price=Min("price"),
#             max_price=Max("price"),
#         ).order_by("date__year", "date__month")

#         data = [
#             {
#                 "period": f"{entry['date__year']}-{entry['date__month']:02d}",
#                 "avg_price": entry["avg_price"],
#                 "avg_open": entry["avg_open"],
#                 "avg_high": entry["avg_high"],
#                 "avg_low": entry["avg_low"],
#                 "avg_percent": entry["avg_percent"],
#                 "avg_diff": entry["avg_diff"],
#                 "min_price": entry["min_price"],
#                 "max_price": entry["max_price"],
#             }
#             for entry in queryset
#         ]

#     else:
#         return JsonResponse({"error": "Invalid 'group_by' parameter. Use 'daily' or 'monthly'."}, status=400)

#     return JsonResponse({"data": data, "count": len(data)})