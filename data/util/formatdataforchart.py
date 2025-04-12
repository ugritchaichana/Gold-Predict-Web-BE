import json
from datetime import datetime


def get_formatted_time_labels(data, timeframe):
    labels = []
    
    for item in data:
        dt = datetime.fromtimestamp(item['timestamp'])
        
        if timeframe == 'day':
            formatted_date = dt.strftime('%d-%m-%Y')
        elif timeframe == 'week':
            year, week_num, _ = dt.isocalendar()
            formatted_date = f"W{week_num}-{year}"
        elif timeframe == 'month':
            formatted_date = dt.strftime('%m-%Y')
        elif timeframe == 'quarter':
            quarter = (dt.month - 1) // 3 + 1
            formatted_date = f"Q{quarter}-{dt.year}"
        elif timeframe == 'year':
            formatted_date = dt.strftime('%Y')
        else:
            formatted_date = dt.strftime('%d-%m-%Y %H:%M')
        
        labels.append(formatted_date)
    
    return labels


def format_data_for_chart(data, data_type, timeframe):
    if not data:
        return {
            'labels': [],
            'datasets': []
        }
    
    # เรียงข้อมูลตาม timestamp
    sorted_data = sorted(data, key=lambda x: x['timestamp'])
    
    # จัดรูปแบบ timestamp ให้เป็นป้ายกำกับ
    labels = get_formatted_time_labels(sorted_data, timeframe)
    
    # สร้าง datasets ตามชนิดของข้อมูล
    datasets = []
    
    if data_type == 'USDTHB':
        # สำหรับข้อมูล USDTHB - แสดงข้อมูล OHLC
        datasets.append({
            'label': 'Open',
            'data': [item.get('open', 0) for item in sorted_data],
        })
        datasets.append({
            'label': 'High',
            'data': [item.get('high', 0) for item in sorted_data],
        })
        datasets.append({
            'label': 'Low',
            'data': [item.get('low', 0) for item in sorted_data],
        })
        datasets.append({
            'label': 'Close',
            'data': [item.get('close', 0) for item in sorted_data],
        })
    elif data_type == 'GOLDTH':
        # สำหรับข้อมูล GOLDTH (ราคาทองคำในไทย)
        datasets.append({
            'label': 'Price',
            'data': [item.get('price', 0) for item in sorted_data],
        })
        datasets.append({
            'label': 'Bar Sell Price (ทองคำแท่ง-ขาย)',
            'data': [item.get('bar_sell_price', 0) for item in sorted_data],
        })
        datasets.append({
            'label': 'Bar Price Change',
            'data': [item.get('bar_price_change', 0) for item in sorted_data],
        })
        datasets.append({
            'label': 'Bar Buy Price (ทองคำแท่ง-ซื้อ)',
            'data': [item.get('bar_buy_price', 0) for item in sorted_data],
        })
        datasets.append({
            'label': 'Ornament Buy Price (ทองรูปพรรณ-ซื้อ)',
            'data': [item.get('ornament_buy_price', 0) for item in sorted_data],
        })
        datasets.append({
            'label': 'Ornament Sell Price (ทองรูปพรรณ-ขาย)',
            'data': [item.get('ornament_sell_price', 0) for item in sorted_data],
        })
    elif data_type == 'GOLDUS':
        # สำหรับข้อมูล GOLDUS (ราคาทองคำในตลาดโลก)
        datasets.append({
            'label': 'Price',
            'data': [item.get('price', 0) for item in sorted_data],
        })
        datasets.append({
            'label': 'Close Price',
            'data': [item.get('close_price', 0) for item in sorted_data],
        })
        datasets.append({
            'label': 'High Price',
            'data': [item.get('high_price', 0) for item in sorted_data],
        })
        datasets.append({
            'label': 'Low Price',
            'data': [item.get('low_price', 0) for item in sorted_data],
        })
        datasets.append({
            'label': 'Volume',
            'data': [item.get('volume', 0) for item in sorted_data],
        })
        datasets.append({
            'label': 'Volume Weight Avg',
            'data': [item.get('volume_weight_avg', 0) for item in sorted_data],
        })
        datasets.append({
            'label': 'Number of Transactions',
            'data': [item.get('num_transactions', 0) for item in sorted_data],
        })
    
    return {
        'labels': labels,
        'datasets': datasets
    }