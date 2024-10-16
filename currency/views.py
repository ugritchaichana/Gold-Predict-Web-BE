import pandas as pd
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from .models import USDTHB, CNYTHB
from .serializers import USDTHBSerializer, CNYTHBSerializer
from datetime import datetime

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

class CurrencyDataListView(APIView):

    def get(self, request, format=None):
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
                data = model.objects.filter(date__range=[start_date, end_date])
            else:
                data = model.objects.all()

            if currency.lower() == 'usd':
                serializer = USDTHBSerializer(data, many=True)
            else:
                serializer = CNYTHBSerializer(data, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response({"error": "Currency not specified."}, status=status.HTTP_400_BAD_REQUEST)


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
