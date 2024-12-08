import os
import requests
from flask import Flask, render_template
from urllib.parse import quote
from dotenv import load_dotenv
import teslapy
import logging
import json

app = Flask(__name__, static_folder='static')
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('app')

# Environment variables
TESLA_EMAIL = os.environ.get('TESLA_EMAIL')
TESLA_REFRESH_TOKEN = os.environ.get('TESLA_REFRESH_TOKEN')
BUNNY_STORAGE_ZONE = os.environ.get('BUNNY_STORAGE_ZONE')
BUNNY_API_KEY = os.environ.get('BUNNY_ACCESS_KEY')
BUNNY_PULL_ZONE_URL = os.environ.get('BUNNY_PULL_ZONE_URL')
MY_CAR_NAME = "MLSII - Tesla 3"

def get_tesla_data():
    """Fetch Tesla vehicle data with detailed error logging."""
    try:
        logger.info("Starting Tesla API connection...")
        logger.info(f"Using refresh token starting with: {TESLA_REFRESH_TOKEN[:50]}...")
        
        with teslapy.Tesla(TESLA_EMAIL) as tesla:
            try:
                # Set refresh token and force token refresh
                tesla.refresh_token = TESLA_REFRESH_TOKEN
                logger.info("Attempting token refresh...")
                tesla.fetch_token()
                logger.info("Token refresh successful")
                
                # Get vehicles
                logger.info("Requesting vehicle list...")
                vehicles = tesla.vehicle_list()
                logger.info(f"Found {len(vehicles)} vehicles")
                
                # Find specific car
                my_car = None
                for vehicle in vehicles:
                    logger.info(f"Checking vehicle: {vehicle['display_name']}")
                    if vehicle['display_name'] == MY_CAR_NAME:
                        my_car = vehicle
                        break

                if not my_car:
                    logger.error(f"Could not find car named {MY_CAR_NAME}")
                    return {'state': 'offline'}

                current_state = my_car['state']
                logger.info(f"Vehicle state: {current_state}")

                if current_state == 'online':
                    try:
                        logger.info("Getting vehicle data...")
                        data = my_car.get_vehicle_data()
                        charge_state = data['charge_state']
                        return {
                            'state': 'online',
                            'battery_level': charge_state['battery_level'],
                            'range': int(charge_state['battery_range'])
                        }
                    except Exception as e:
                        logger.error(f"Error getting vehicle data: {str(e)}")
                        return {'state': current_state}
                else:
                    try:
                        logger.info("Attempting to wake vehicle...")
                        my_car.sync_wake_up()
                        return {'state': 'waking_up'}
                    except Exception as e:
                        logger.error(f"Error waking vehicle: {str(e)}")
                        return {'state': current_state}

            except Exception as e:
                logger.error(f"Tesla API operation failed: {str(e)}")
                return {'state': 'error'}

    except Exception as e:
        logger.error(f"Tesla connection failed: {str(e)}")
        return {'state': 'error'}

def get_media_from_bunny():
    """Fetch media files from BunnyCDN."""
    if not all([BUNNY_STORAGE_ZONE, BUNNY_API_KEY, BUNNY_PULL_ZONE_URL]):
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
    except Exception:
        return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/tesla')
def tesla():
    tesla_data = get_tesla_data()
    return render_template('tesla.html', tesla_data=tesla_data)

@app.route('/portfolio')
def portfolio():
    portfolio_items = get_media_from_bunny()
    return render_template('portfolio.html', portfolio_items=portfolio_items)

@app.route('/links')
def links():
    return render_template('links.html')

if __name__ == '__main__':
    app.run(debug=True)