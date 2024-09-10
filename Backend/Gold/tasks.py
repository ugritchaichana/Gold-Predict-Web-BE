# your_app/tasks.py
from celery import shared_task
import requests
from bs4 import BeautifulSoup
from django.utils import timezone
from .models import GoldPrice
from .serializers import DailyGoldPriceSerializer

@shared_task
def scrape_gold_price():
    url = 'https://www.goldtraders.or.th/'
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        span_element = soup.find('span', id='DetailPlace_uc_goldprices1_lblBLSell')

        if span_element:
            try:
                price = float(span_element.get_text(strip=True).replace(',', ''))

                data = {
                    'date': timezone.now().date(),
                    'gold_price': price
                }
                
                serializer = DailyGoldPriceSerializer(data=data)
                if serializer.is_valid():
                    serializer.save()
                    return 'Success'
                else:
                    return f'Error: {serializer.errors}'
            except ValueError:
                return 'Invalid price format'

        return 'Price element not found'

    return f'Failed to retrieve data: {response.status_code}'


@shared_task
def test_task():
    print('Test Task Executed')
    return 'Task executed!'
