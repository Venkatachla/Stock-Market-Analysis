#!/usr/bin/env python3
"""Test the /predict endpoint."""
import requests
import json
from time import sleep

sleep(2)

print('Testing /predict endpoint')
print('=' * 60)

try:
    r = requests.get('http://localhost:8000/predict?symbol=RELIANCE.NS', timeout=15)
    print(f'Status: {r.status_code}')

    if r.status_code == 200:
        data = r.json()
        print('Response:')
        print(json.dumps(data, indent=2))
    else:
        print(f'Error: {r.text[:500]}')
except Exception as e:
    print(f'Connection error: {e}')
