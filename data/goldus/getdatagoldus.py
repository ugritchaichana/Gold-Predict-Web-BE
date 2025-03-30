import requests
from datetime import datetime, timedelta

def get_data_goldus(start_str, end_str):
    print(f"get_data_goldus : {start_str} to end : {end_str}")

    if isinstance(start_str, int) or start_str.isdigit():
        start_date = datetime.utcfromtimestamp(int(start_str))
    else:
        start_date = datetime.strptime(start_str, '%d-%m-%y')

    if isinstance(end_str, int) or end_str.isdigit():
        end_date = datetime.utcfromtimestamp(int(end_str))
    else:
        end_date = datetime.strptime(end_str, '%d-%m-%y')
    
    all_data = []
    current_date = start_date
    print(f"start : {start_date} to end : {end_date} and current_date : {current_date}")
    
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        url = f'https://www.finnomena.com/fn3/api/polygon/gold/spot/v2/aggs/ticker/C%3AXAUUSD/range/1/hour/{date_str}/{date_str}'
        print(f"Fetching data for date: {date_str} URL: {url}")

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            print(f"Response for {date_str}: {data}")

            if data.get('statusOK') and 'results' in data['data']:
                all_data.extend(data['data']['results'])

        except requests.exceptions.RequestException as e:
            print(f"Error fetching data for {date_str}: {e}")
        
        current_date += timedelta(days=1)
    
    print(f"Final data collected: {all_data}")
    return all_data