import requests
import logging
from google.cloud import logging as gcloud_logging
import functions_framework

# Set up Google Cloud Logging
client = gcloud_logging.Client()
client.setup_logging()

# URLs
currency_url = "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.json"
add_currency_url = "http://34.1.193.71:8000/currency/add-crrencyth/"
gold_data_urls = [
    "http://34.1.193.71:8000/finnomenaGold/fetch-gold-data/?db_choice=0",
    "http://34.1.193.71:8000/finnomenaGold/fetch-gold-data/?db_choice=1"
]

@functions_framework.http
def fetch_and_post_data(request):
    """HTTP Cloud Function to fetch data and post it.
    
    Args:
        request (flask.Request): The request object.
        
    Returns:
        The response text.
    """
    # Trigger gold data fetch
    for url in gold_data_urls:
        gold_response = requests.get(url)
        if gold_response.status_code == 200:
            logging.info(f"Successfully triggered gold data fetch: {url}")
            logging.info(f"Response Data: {gold_response.json()}")  # Log the response data
        else:
            logging.error(f"Failed to trigger gold data fetch: {url}, Status code: {gold_response.status_code}")
            logging.error(f"Error Response: {gold_response.text}")  # Log the error message

    # Request data from the external currency API
    response = requests.get(currency_url)

    if response.status_code == 200:
        data = response.json()
        date = data.get('date')
        thb = data.get('usd', {}).get('thb')
        
        # Log successful retrieval
        logging.info(f"Date: {date}, THB: {thb}")
        
        # Create payload for the POST request
        payload = {'date': date, 'price': thb}
        
        # Post data to the server
        post_response = requests.post(add_currency_url, json=payload)
        logging.info(f"POST status code: {post_response.status_code}")
        
        if post_response.status_code == 201:
            logging.info("Data added successfully!")
            return 'Data added successfully!', 200
        else:
            logging.error(f"Failed to add data. Status code: {post_response.status_code} {post_response.text}")
            return f"Failed to add data. Status code: {post_response.status_code}", 400
    else:
        logging.error(f"Failed to retrieve data. Status code: {response.status_code}")
        return f"Failed to retrieve data. Status code: {response.status_code}", 400
