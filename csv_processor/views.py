import os
import pandas as pd
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from google.cloud import storage
from django.conf import settings
from datetime import datetime
from .models import us_xau

class UploadCSV_XAUUSD(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        file_obj = request.FILES['file']
        
        df = pd.read_csv(file_obj)
        
        df.columns = ['Date', 'Price', 'Open', 'High', 'Low', 'Volume', 'Change']
        
        for column in ['Price', 'Open', 'High', 'Low', 'Volume']:
            if df[column].dtype == 'object':
                df[column] = df[column].str.replace(',', '', regex=False)
            df[column] = pd.to_numeric(df[column], errors='coerce').round(2)

        df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')
        df.set_index('Date', inplace=True)
        df = df.resample('D').asfreq()
        df[['Price', 'Open', 'High', 'Low', 'Volume']] = df[['Price', 'Open', 'High', 'Low', 'Volume']].interpolate()

        df['Unit'] = df['Price'].diff().round(2)
        df['Unit'] = df['Unit'].fillna(0)

        df['Change'] = df['Change'].str.replace('%', '', regex=False)
        df['Change'] = pd.to_numeric(df['Change'], errors='coerce').round(2)

        df = df.replace([float('inf'), float('-inf'), pd.NA], None)

        if df.isnull().values.any():
            df = df.fillna(0)

        df.index = df.index.strftime('%Y-%m-%d')
        df.reset_index(inplace=True)

        latest_price = df['Price'].iloc[-1] if not df.empty else 0

        gold_price_entries = []
        for _, row in df.iterrows():
            gold_price_entries.append(
                us_xau(
                    date=row['Date'],
                    price=row['Price'],
                    open=row['Open'],
                    high=row['High'],
                    low=row['Low'],
                    volume=row['Volume'],
                    percent=row['Change'],
                    unitUSD=round(latest_price - row['Price'], 2),
                    unitTHB=0,
                )
            )

        us_xau.objects.bulk_create(gold_price_entries)

        current_time = datetime.now().strftime('%H-%M-%d-%m-%y')
        output_file_path = os.path.join(settings.BASE_DIR, f'output_data-({current_time}).csv')
        df.to_csv(output_file_path, index=False)

        client = storage.Client.from_service_account_json(settings.SERVICE_ACCOUNT_FILE)
        bucket = client.bucket(settings.GCS_BUCKET_NAME)
        output_file_name = f'XAU-US-({current_time}).csv'

        destination_blob_name = 'run-sources-monterrey-433913-r6-us-central1/csv/xau-usd/' + output_file_name
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(output_file_path)

        return Response(df.to_dict(orient='records'), status=status.HTTP_200_OK)
