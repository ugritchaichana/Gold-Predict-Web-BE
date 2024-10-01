import csv
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from Gold_US.serializers import GoldPriceXAUAPISerializer, CSVUploadSerializer
from Gold_US.models import GoldPriceXAU_API

class CSVUploadView(APIView):

    def post(self, request, *args, **kwargs):
        serializer = CSVUploadSerializer(data=request.data)

        if serializer.is_valid():
            file = serializer.validated_data['file']
            decoded_file = file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)

            for row in reader:
                data = {
                    'date': row['Date'],
                    'price': row['Price'],
                    'open': row['Open'],
                    'high': row['High'],
                    'low': row['Low'],
                    'volume': row['Volume'],
                    'percent': row['Percent'],
                    'unitUSD': row['Unit'],
                    'unitTHB': '0'
                }

                gold_price_serializer = GoldPriceXAUAPISerializer(data=data)
                if gold_price_serializer.is_valid():
                    gold_price_serializer.save()
                else:
                    return Response(gold_price_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            return Response({"message": "CSV uploaded and data saved successfully"}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
