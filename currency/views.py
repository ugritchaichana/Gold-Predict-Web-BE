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
import requests
from django.http import JsonResponse
from django.core.cache import cache
import logging
from django.conf import settings
import gc

# Set cache timeout (in seconds)
CACHE_TIMEOUT = 3600  # 1 hour

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


@csrf_exempt
def update_daily_usdthb(request):
    """
    Fetch latest USD to THB exchange rate data and store it in the database.
    Uses the exchangerate-api.com 'latest' endpoint to get current rates.
    
    Parameters:
    - update_existing (optional): Set to 'true' to update existing records for today's date
    """
    try:
        # Get the API key from environment variables using decouple
        from decouple import config
        api_key = config('EXCHANGERATE_API_KEY', default=None)
        if not api_key:
            logger.error("API key not found in environment variables")
            return JsonResponse({"error": "API key not found in environment variables"}, status=400)
        
        # Get update_existing parameter
        update_existing = request.GET.get('update_existing', 'false').lower() == 'true'
        
        # Fetch data from the exchangerate API using the 'latest' endpoint
        url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/USD"
        logger.info(f"Making API request to: {url}")
        print(f"Making API request to: {url}")  # For debugging purposes
        
        # Import requests library if not already imported
        import requests
        response = requests.get(url)
        
        if response.status_code != 200:
            logger.error(f"API request failed with status code: {response.status_code}")
            return JsonResponse({"error": f"Failed to fetch data from API: {response.status_code}"}, status=500)
        
        data = response.json()
        
        if data.get('result') != 'success':
            error_msg = data.get('error', 'Unknown error')
            logger.error(f"API returned error: {error_msg}")
            return JsonResponse({"error": f"API returned error: {error_msg}"}, status=500)
        
        # Extract time_last_update_utc for date and parse it
        time_last_update_utc = data.get('time_last_update_utc')
        if not time_last_update_utc:
            logger.error("No update time found in API response")
            return JsonResponse({"error": "No update time found in API response"}, status=500)
        
        # Example format: "Fri, 18 Apr 2025 00:00:01 +0000"
        try:
            # Parse the datetime from the UTC string
            update_datetime = datetime.strptime(time_last_update_utc, "%a, %d %b %Y %H:%M:%S %z")
            # Convert to date object
            target_date = update_datetime.date()
        except ValueError as e:
            logger.error(f"Failed to parse date from API response: {e}")
            return JsonResponse({"error": f"Failed to parse date from API response: {e}"}, status=500)
        
        target_date_str = target_date.strftime('%Y-%m-%d')
        formatted_date_str = target_date.strftime('%d-%m-%y')  # Format as dd-mm-yy
        logger.info(f"Extracted date from API: {target_date_str}, formatted as: {formatted_date_str}")        # Check if we already have data for the target date
        existing_record = USDTHB.objects.filter(date=target_date).first()
        
        # For scheduled tasks, set auto parameter to true to update data automatically
        auto_update = request.GET.get('auto', 'false').lower() == 'true'
        if auto_update:
            update_existing = True
            logger.info(f"Auto update mode enabled, will update existing records if found")
            
        if existing_record and not update_existing:
            logger.info(f"Data for {target_date_str} already exists in database")
            return JsonResponse({
                "message": f"Data for {target_date_str} already exists in database", 
                "data": {
                    "id": existing_record.id,
                    "date": existing_record.date.strftime('%Y-%m-%d'),
                    "price": existing_record.price,
                    "open": existing_record.open,
                    "high": existing_record.high,
                    "low": existing_record.low,
                    "percent": existing_record.percent,
                    "diff": existing_record.diff
                }
            })
        
        # Get data from the previous day to calculate percent and diff
        day_before = target_date - timedelta(days=1)
        previous_record = USDTHB.objects.filter(date=day_before).first()
        
        # Initialize values
        diff = 0
        percent = 0
        thb_rate = None
        open_price = None
        high = None
        low = None
        
        # Try to get complete OHLC data from Alpha Vantage (primary source)
        try:
            # You'll need to sign up for a free API key at https://www.alphavantage.co/
            alpha_vantage_api_key = config('ALPHA_VANTAGE_API_KEY', default=None)
            
            if alpha_vantage_api_key:
                # Use FX_DAILY endpoint to get daily forex data
                av_url = f"https://www.alphavantage.co/query?function=FX_DAILY&from_symbol=USD&to_symbol=THB&apikey={alpha_vantage_api_key}"
                logger.info(f"Making Alpha Vantage API request for OHLC data (primary source)")
                
                av_response = requests.get(av_url)
                if av_response.status_code == 200:
                    av_data = av_response.json()
                    time_series = av_data.get('Time Series FX (Daily)', {})
                    
                    # Find the data for our target date
                    target_date_str_dash = target_date.strftime('%Y-%m-%d')
                    if target_date_str_dash in time_series:
                        day_data = time_series[target_date_str_dash]
                        # Get complete OHLC values
                        open_price = float(day_data.get('1. open'))
                        high = float(day_data.get('2. high'))
                        low = float(day_data.get('3. low'))
                        thb_rate = float(day_data.get('4. close'))  # Use close as price
                        
                        logger.info(f"Got complete OHLC data from Alpha Vantage: O: {open_price}, H: {high}, L: {low}, C: {thb_rate}")
                    else:
                        logger.warning(f"Target date {target_date_str_dash} not found in Alpha Vantage data")
                        raise ValueError("Date not found in Alpha Vantage data")
                else:
                    logger.warning(f"Alpha Vantage API returned status code: {av_response.status_code}")
                    raise ValueError(f"Alpha Vantage API error: {av_response.status_code}")
            else:
                logger.warning("No Alpha Vantage API key found, falling back to Exchange Rate API")
                raise ValueError("No Alpha Vantage API key")
                
        except Exception as e:
            logger.warning(f"Failed to get OHLC data from Alpha Vantage: {e}")
            logger.info(f"Falling back to Exchange Rate API for price data")
            
            # Fall back to Exchange Rate API for at least the closing price
            # Get THB rate from conversion_rates
            conversion_rates = data.get('conversion_rates', {})
            thb_rate = conversion_rates.get('THB')
            if not thb_rate:
                logger.error("THB rate not found in Exchange Rate API response")
                return JsonResponse({"error": "THB rate not found in API response"}, status=500)
            
            logger.info(f"THB exchange rate from fallback source: {thb_rate}")
            
            # Estimate OHLC values if we couldn't get them from Alpha Vantage
            open_price = thb_rate  # Default if we can't calculate
            high = thb_rate * 1.002  # Estimate high as 0.2% above closing
            low = thb_rate * 0.998   # Estimate low as 0.2% below closing
        
        if previous_record and previous_record.price:
            diff = thb_rate - previous_record.price
            percent = (diff / previous_record.price) * 100
            # Only use previous day's price as open if we couldn't get better data
            if open_price == thb_rate:
                open_price = previous_record.price
                
        # Round all values to 2 decimal places for consistency
        thb_rate = round(thb_rate, 2)
        open_price = round(open_price, 2)
        high = round(high, 2)
        low = round(low, 2)
        percent = round(percent, 2)
        diff = round(diff, 2)
        
        # Create or update USDTHB record
        if existing_record and update_existing:
            existing_record.price = thb_rate
            existing_record.open = open_price
            existing_record.high = high
            existing_record.low = low
            existing_record.percent = percent
            existing_record.diff = diff
            existing_record.save()
            new_record = existing_record
            action = "updated"
        else:
            new_record = USDTHB(
                date=target_date,
                price=thb_rate,
                open=open_price,
                high=high,
                low=low,
                percent=percent,
                diff=diff
            )
            new_record.save()
            action = "created"
        
        # Clear variables to free memory
        data = None
        response = None
        import gc
        gc.collect()
        
        return JsonResponse({
            "message": f"Exchange rate data for {target_date_str} fetched and {action} successfully",
            "data": {
                "id": new_record.id,
                "date": new_record.date.strftime('%Y-%m-%d'),
                "price": new_record.price,
                "open": new_record.open,
                "high": new_record.high,
                "low": new_record.low,
                "percent": new_record.percent,
                "diff": new_record.diff
            }
        })
        
    except Exception as e:
        logger.error(f"Error in update_daily_usdthb: {str(e)}")
        return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)


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

def convert_dates_to_str(obj):
    import datetime
    if isinstance(obj, dict):
        return {k: convert_dates_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_dates_to_str(i) for i in obj]
    elif isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    else:
        return obj

def get_currency_data(request):
    frame = request.GET.get('frame', None)
    start_date = request.GET.get('start', None)
    end_date = request.GET.get('end', None)
    group_by = request.GET.get('group_by', 'daily')
    max_points = request.GET.get('max')  # Add max parameter support
    display = request.GET.get('display')  # Add display parameter for chart view

    # Using the global CACHE_TIMEOUT constant
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
          # Cache key - include all parameters that affect the result
    cache_key = f"currency_data:{start_date}:{end_date}:{frame}:{group_by}:{max_points}:{display}"
    logger.info(f"Generated cache key: {cache_key}")

    # Check Cache first
    if use_cache:
        cached_data = cache.get(cache_key)
        if cached_data:
            try:
                if display == 'chart2':
                    return JsonResponse(list(cached_data), safe=False)
                cached_data = json.loads(cached_data)
                logger.info(f"Cache hit: Using cached data for key: {cache_key}")
                
                # If the request is for chart data
                if display == 'chart' and "chart_data" in cached_data:
                    return JsonResponse({
                        "status": "success",
                        "data": cached_data["chart_data"],
                        "start_date": start_date.strftime('%Y-%m-%d') if start_date else None,
                        "end_date": end_date.strftime('%Y-%m-%d') if end_date else None,
                        "default_dates_used": {
                            "start": start_date.strftime('%d-%m-%Y') if start_date else None,
                            "end": end_date.strftime('%d-%m-%Y') if end_date else None
                        }
                    })
                
                # For regular data
                if "data" in cached_data:
                    return JsonResponse({
                        "cache": [{"status": "used cache", "database": "redis"}],
                        "count": len(cached_data["data"]),
                        "data": cached_data["data"]
                    })
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
        return JsonResponse({"error": "Invalid 'group_by' parameter. Use 'daily' or 'monthly'."}, status=400)    # Format data for chart if requested
    if display == 'chart':
        chart_data = format_chart_data_usdthb(data)
        if use_cache:
            chart_data_serialized = convert_dates_to_str(chart_data)
            cache.set(cache_key, json.dumps({"chart_data": chart_data_serialized}), timeout=CACHE_TIMEOUT)
            logger.info(f"Cached chart data for key: {cache_key}")
        
        return JsonResponse({
            "status": "success",
            "data": chart_data,
            "start_date": start_date.strftime('%Y-%m-%d') if start_date else None,
            "end_date": end_date.strftime('%Y-%m-%d') if end_date else None,
            "default_dates_used": {
                "start": start_date.strftime('%d-%m-%Y') if start_date else None,
                "end": end_date.strftime('%d-%m-%Y') if end_date else None
            }
        })
    elif display == 'chart2':
     try:
        # chart_data = format_chart_data_usdthb(data)
        result =[{
            "open":line['open'],
            "high":line['high'],
            "low":line['low'],
            "close":line['price'],
            "timestamp":int(datetime.combine(line['date'], datetime.min.time()).timestamp())
        }
        for line in data
        ]
        
        # if use_cache:
        #     chart_data_serialized = convert_dates_to_str(chart_data)
        #     cache.set(cache_key, json.dumps({"chart_data": chart_data_serialized}), timeout=CACHE_TIMEOUT)
        #     logger.info(f"Cached chart data for key: {cache_key}")
        cache.set(cache_key, result, timeout=CACHE_TIMEOUT)
        return JsonResponse(list(result), safe=False)
     except Exception as e:
         return JsonResponse({
             "error":str(e)
         },status=400)
    # For regular data display
    serialized_data = serialize_data(data)
    
    if use_cache:
        # Convert Python Object to JSON String before storing in Redis
        cache.set(cache_key, json.dumps({"data": serialized_data}), timeout=CACHE_TIMEOUT)
        logger.info(f"Cached data for key: {cache_key}")

    # Return response with the cache source
    return JsonResponse({
        "cache": [{"status": "no used cache", "database": "postgresql"}],
        "count": len(serialized_data),
        "data": serialized_data
    })

def format_chart_data_usdthb(data):
    """
    Format USDTHB data for chart display similar to finnomenaGold
    """
    labels = []
    dates = []
    price_data = []
    open_data = []
    high_data = []
    low_data = []
    percent_data = []
    diff_data = []
    
    for item in data:
        # Format date for labels
        date_str = item.get('date')
        if isinstance(date_str, str):
            labels.append(date_str)
        elif hasattr(date_str, 'strftime'):
            labels.append(date_str.strftime('%Y-%m-%d'))
        else:
            labels.append('')
        
        # Store date values
        dates.append(item.get('date', ''))
        
        # Store numerical data with proper type conversion
        price_data.append(float(item.get('price', 0)) if item.get('price') is not None else 0)
        open_data.append(float(item.get('open', 0)) if item.get('open') is not None else 0)
        high_data.append(float(item.get('high', 0)) if item.get('high') is not None else 0)
        low_data.append(float(item.get('low', 0)) if item.get('low') is not None else 0)
        percent_data.append(float(item.get('percent', 0)) if item.get('percent') is not None else 0)
        diff_data.append(float(item.get('diff', 0)) if item.get('diff') is not None else 0)
    
    return {
        "labels": labels,
        "datasets": [
            { "label": "Date", "data": dates },
            { "label": "Price", "data": price_data },
            { "label": "Open", "data": open_data },
            { "label": "High", "data": high_data },
            { "label": "Low", "data": low_data },
            { "label": "Percent Change", "data": percent_data },
            { "label": "Difference", "data": diff_data }
        ]
    }
