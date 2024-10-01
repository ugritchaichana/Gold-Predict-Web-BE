import requests
from datetime import datetime, timedelta
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import GoldPriceTH
from .serializers import GoldPriceSerializer
from django.utils import timezone

@api_view(['POST'])
def fetch_gold_th(request):
    from_date = request.data.get('from')
    to_date = request.data.get('to')

    if not from_date or not to_date:
        return Response({"error": "Please provide both 'from' and 'to' dates."}, status=400)

    try:
        from_timestamp = int(datetime.strptime(from_date, '%Y-%m-%d').timestamp())
        to_timestamp = int(datetime.strptime(to_date, '%Y-%m-%d').timestamp())
    except ValueError:
        return Response({"error": "Invalid date format. Use 'YYYY-MM-DD'."}, status=400)

    api_url = f"https://www.finnomena.com/fn3/api/gold/trader/tv/history?symbol=trader_bar&resolution=1D&from={from_timestamp}&to={to_timestamp}"
    response = requests.get(api_url)

    if response.status_code == 200:
        data = response.json()
        timestamps = data.get('t', [])
        prices = data.get('c', [])

        previous_price = None
        previous_date = None
        current_date = None

        for i, ts in enumerate(timestamps):
            current_date = datetime.utcfromtimestamp(ts)
            current_date = timezone.make_aware(current_date)
            price = float(prices[i])

            if previous_date is not None:
                while previous_date + timedelta(days=1) < current_date:
                    previous_date += timedelta(days=1)
                    GoldPriceTH.objects.create(
                        date=previous_date,
                        price=previous_price if previous_price is not None else 0,
                        price_diff_unit=0,
                        price_diff_percent=0
                    )

            if previous_price is not None:
                price_diff_unit = price - previous_price
                price_diff_percent = (price_diff_unit / previous_price) * 100
            else:
                price_diff_unit = 0
                price_diff_percent = 0 

            GoldPriceTH.objects.create(
                date=current_date,
                price=price,
                price_diff_unit=price_diff_unit,
                price_diff_percent=price_diff_percent
            )

            previous_price = price
            previous_date = current_date

        return Response({"message": "Data fetched and saved successfully!"}, status=201)
    else:
        return Response({"error": "Unable to fetch data from API"}, status=500)
