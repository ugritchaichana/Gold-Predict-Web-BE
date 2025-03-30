import random
import time
from datetime import datetime, timezone
import cloudscraper
from datetime import timedelta

MAX_ITEMS = 5000
RESOLUTION_MINUTES = 60
SECONDS_PER_ITEM = RESOLUTION_MINUTES * 60
MAX_DELTA_SECONDS = MAX_ITEMS * SECONDS_PER_ITEM
MAX_DELTA = timedelta(seconds=MAX_DELTA_SECONDS)


def get_data_usdthb(start_ts, end_ts):
    start_dt = datetime.utcfromtimestamp(start_ts).replace(tzinfo=timezone.utc)
    end_dt = datetime.utcfromtimestamp(end_ts).replace(tzinfo=timezone.utc)
    
    if start_dt > end_dt:
        raise ValueError("Start time cannot be greater than end time.")

    current_start = start_dt
    all_data = []
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
    ]

    while current_start < end_dt:
        current_end = min(current_start + MAX_DELTA, end_dt)
        
        url = (
            f'https://tvc4.investing.com/57c182657e622fb4e391a1c95dbc2589/'
            f'1742541167/1/1/8/history?symbol=147&resolution={RESOLUTION_MINUTES}&'
            f'from={int(current_start.timestamp())}&to={int(current_end.timestamp())}'
        )

        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Referer': 'https://www.investing.com/currencies/usd-thb',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
        
        time.sleep(random.uniform(1, 3))
        
        scraper = cloudscraper.create_scraper()
        response = scraper.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        parsed_data = response.json()
        
        if parsed_data.get('s') != 'ok':
            raise RuntimeError(f"API error: {parsed_data.get('s', 'Unknown error')}")
        
        try:
            timestamps = parsed_data["t"]
            close_prices = parsed_data["c"]
            open_prices = parsed_data["o"]
            high_prices = parsed_data["h"]
            low_prices = parsed_data["l"]
        except KeyError as e:
            raise RuntimeError(f"Unexpected response format: Missing key {e}") from e

        for i in range(len(timestamps)):
            all_data.append({
                "timestamp": timestamps[i],
                "date": datetime.utcfromtimestamp(timestamps[i]).strftime('%d-%m-%Y'),
                "close": close_prices[i],
                "open": open_prices[i],
                "high": high_prices[i],
                "low": low_prices[i]
            })

        current_start = current_end

    return all_data