import os
import requests
from flask import Flask, render_template
from urllib.parse import quote
from dotenv import load_dotenv
import teslapy
import time
import json
from datetime import datetime, timedelta

app = Flask(__name__)
load_dotenv()

# Environment variables with fallbacks for better error handling
BUNNY_STORAGE_ZONE = os.environ.get('BUNNY_STORAGE_ZONE')
BUNNY_API_KEY = os.environ.get('BUNNY_ACCESS_KEY')
BUNNY_PULL_ZONE_URL = os.environ.get('BUNNY_PULL_ZONE_URL')
TESLA_EMAIL = os.environ.get('TESLA_EMAIL')
TESLA_REFRESH_TOKEN = os.environ.get('TESLA_REFRESH_TOKEN')
MY_CAR_NAME = "MLSII - Tesla 3"

def refresh_tesla_token():
    """Get a new access token using refresh token."""
    try:
        url = "https://auth.tesla.com/oauth2/v3/token"
        headers = {"Content-Type": "application/json"}
        data = {
            "grant_type": "refresh_token",
            "client_id": "ownerapi",
            "refresh_token": TESLA_REFRESH_TOKEN,
            "scope": "openid email offline_access"
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()['access_token']
    except Exception as e:
        print(f"Error refreshing token: {e}")
        return None

def get_tesla_data():
    """Fetch Tesla vehicle data with improved error handling."""
    try:
        if not TESLA_EMAIL or not TESLA_REFRESH_TOKEN:
            print("Tesla credentials not configured in environment")
            return None

        print("\nAttempting to connect to Tesla API...")
        tesla = teslapy.Tesla(TESLA_EMAIL)
        
        # Use refresh token flow
        access_token = refresh_tesla_token()
        if not access_token:
            return None
            
        tesla.token['access_token'] = access_token
        
        print("Getting vehicle list...")
        vehicles = tesla.vehicle_list()
        if not vehicles:
            print("No vehicles found")
            return None

        # Find specific car
        my_car = None
        for v in vehicles:
            print(f"Found vehicle: {v['display_name']}")
            if v['display_name'] == MY_CAR_NAME:
                my_car = v
                break
        
        if not my_car:
            print(f"Could not find car named {MY_CAR_NAME}")
            return None

        current_state = my_car['state']
        print(f"Car state: {current_state}")
        
        # If vehicle is online, get detailed data
        if current_state == 'online':
            try:
                print("Getting vehicle data...")
                data = my_car.get_vehicle_data()
                charge_state = data['charge_state']
                
                return {
                    'battery_level': charge_state['battery_level'],
                    'range': int(charge_state['battery_range']),
                    'state': 'online'
                }
            except Exception as e:
                print(f"Failed to get vehicle data: {e}")
                return {'state': current_state}
        else:
            return {'state': current_state}
                
    except Exception as e:
        print(f"Tesla API Error: {str(e)}")
        return None

def get_media_from_bunny():
    """Fetch media files from BunnyCDN."""
    if not all([BUNNY_STORAGE_ZONE, BUNNY_API_KEY, BUNNY_PULL_ZONE_URL]):
        print("Bunny CDN credentials not configured")
        return []

    url = f"https://la.storage.bunnycdn.com/{BUNNY_STORAGE_ZONE}/"
    headers = {"AccessKey": BUNNY_API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        files = response.json()
        
        media = []
        for file in files:
            if not file.get('IsDirectory'):
                file_ext = file['ObjectName'].lower()
                if any(file_ext.endswith(ext) for ext in ('.jpg', '.jpeg', '.png', '.gif', '.mp4')):
                    media.append({
                        "url": f"{BUNNY_PULL_ZONE_URL}/{quote(file['ObjectName'])}",
                        "description": file['ObjectName'].split('.')[0],
                        "type": "video" if file_ext.endswith('.mp4') else "image"
                    })
        return media
    except Exception as e:
        print(f"Error: {str(e)}")
        return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/portfolio')
def portfolio():
    portfolio_items = get_media_from_bunny()
    return render_template('portfolio.html', portfolio_items=portfolio_items)

@app.route('/tesla')
def tesla():
    tesla_data = get_tesla_data()
    return render_template('tesla.html', tesla_data=tesla_data)

@app.route('/links')
def links():
    return render_template('links.html')

if __name__ == '__main__':
    app.run(debug=True)