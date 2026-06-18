import requests
import json

token = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiIzODIxMTIiLCJqdGkiOiI2YTMzNjYxYzg3YjAyMTNhY2FiZjJlNGEiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaXNFeHRlbmRlZCI6dHJ1ZSwiaWF0IjoxNzgxNzUzMzcyLCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE4MTMzNTYwMDB9.U4Ui_7TP5M3b7iVeIEYs15pIkDJHBTdjkr0PHrIvgVI"

url = "https://api.upstox.com/v2/option/chain?instrument_key=NSE_INDEX|Nifty%2050&expiry_date=2026-06-25" 

headers = {
    'Accept': 'application/json',
    'Authorization': f'Bearer {token}'
}

try:
    res = requests.get(url, headers=headers, timeout=5)
    print("Status:", res.status_code)
    if res.status_code == 200:
        data = res.json().get('data', [])
        print("Data items:", len(data))
    else:
        print("Response:", res.text)
except Exception as e:
    print("Error:", e)
