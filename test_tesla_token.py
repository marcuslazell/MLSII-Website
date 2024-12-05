import requests
import os
from dotenv import load_dotenv

load_dotenv()

TESLA_TOKEN = os.getenv('TESLA_REFRESH_TOKEN')

def test_token():
    base_url = "https://owner-api.teslamotors.com/api/1"
    headers = {
        "Authorization": f"Bearer {TESLA_TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }

    print("Testing Tesla API connection...")
    print(f"Using token: {TESLA_TOKEN[:50]}...")
    
    try:
        response = requests.get(f"{base_url}/vehicles", headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_token()