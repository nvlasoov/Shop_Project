import os

from dotenv import load_dotenv
from requests import request

path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(path):
    load_dotenv(path)
    APP_ID = os.environ.get('APP_ID')

def latest():
    response = request(
        method='GET',
        url='https://openexchangerates.org/api/latest.json',
        params={
            'app_id': APP_ID,
            'base': 'USD'
        }
    )
    if response.status_code == 200:
        return {
            'USD': 1,
            **response.json()['rates']
        }
    return {}