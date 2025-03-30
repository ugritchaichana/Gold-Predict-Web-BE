import json
from datetime import datetime


def format_data_for_chart(data, data_type):
    if not data:
        return {"labels": [], "datasets": []}
    
    data = sorted(data, key=lambda x: x['timestamp'])
    
    if data_type == 'USDTHB':
        labels_time = [datetime.fromtimestamp(item['timestamp']).strftime('%d-%m-%Y %H:%M') for item in data]
        
        return {
            "Time": labels_time,
            "datasets": [
                {
                    "label": "Price",
                    "data": [item['close'] for item in data],
                },
                {
                    "label": "Close",
                    "data": [item['close'] for item in data],
                },
                {
                    "label": "Open",
                    "data": [item['open'] for item in data],
                },
                {
                    "label": "High",
                    "data": [item['high'] for item in data],
                },
                {
                    "label": "Low",
                    "data": [item['low'] for item in data],
                }
            ]
        }
    
    elif data_type == 'GOLDTH':
        labels_time = [datetime.fromtimestamp(item['timestamp']).strftime('%d-%m-%Y %H:%M') for item in data]
        
        return {
            "Time": labels_time,
            "datasets": [
                {
                    "label": "Price",
                    "data": [item['bar_sell_price'] for item in data],
                },
                {
                    "label": "Bar Sell Price",
                    "data": [item['bar_sell_price'] for item in data],
                },
                {
                    "label": "Ornament Buy Price",
                    "data": [item['ornament_buy_price'] for item in data],
                },
                {
                    "label": "Ornament Sell Price",
                    "data": [item['ornament_sell_price'] for item in data],
                },
                {
                    "label": "Price Change",
                    "data": [item['bar_price_change'] for item in data],
                }
            ]
        }
    
    elif data_type == 'GOLDUS':
        labels_time = [datetime.fromtimestamp(item['timestamp']).strftime('%d-%m-%Y %H:%M') for item in data]

        return {
            "Time": labels_time,
            "datasets": [
                {
                    "label": "Price",
                    "data": [item['price'] for item in data],
                },
                {
                    "label": "Close Price",
                    "data": [item['close_price'] for item in data],
                },
                {
                    "label": "High Price",
                    "data": [item['high_price'] for item in data],
                },
                {
                    "label": "Low Price",
                    "data": [item['low_price'] for item in data],
                },
                {
                    "label": "Volume",
                    "data": [item['volume'] for item in data],
                }
            ]
        }
    
    return {"labels": [], "datasets": []}