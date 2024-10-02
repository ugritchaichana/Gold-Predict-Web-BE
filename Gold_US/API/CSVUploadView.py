import csv
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from Gold_US.serializers import GoldPriceXAUAPISerializer, CSVUploadSerializer
from Gold_US.models import GoldPriceUS
from datetime import datetime

class CSVUploadView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = CSVUploadSerializer(data=request.data)

        if serializer.is_valid():
            file = serializer.validated_data['file']
            decoded_file = file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)

            gold_prices = []
            
            for row in reader:
                date_str = row['Date']
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                formatted_date = date_obj.strftime('%Y-%m-%d')

                data = GoldPriceUS(
                    date=formatted_date,
                    price=row['Price'],
                    open=row['Open'],
                    high=row['High'],
                    low=row['Low'],
                    volume=row['Volume'],
                    percent=row['Percent'],
                    unitUSD=row['Unit'],
                    unitTHB='0'
                )
                gold_prices.append(data)

            GoldPriceUS.objects.bulk_create(gold_prices)

            return Response({"message": "CSV uploaded and data saved successfully"}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
