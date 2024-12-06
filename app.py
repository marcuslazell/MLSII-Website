import os
import requests
from flask import Flask, render_template
from urllib.parse import quote
from dotenv import load_dotenv
import teslapy
import time
import json
import logging

app = Flask(__name__, static_folder='static')
load_dotenv()

# this comment means nothing
# Add a small delay to ensure environment variables are loaded
time.sleep(2)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('app')

# Environment variables with fallbacks for better error handling
BUNNY_STORAGE_ZONE = os.environ.get('BUNNY_STORAGE_ZONE')
BUNNY_API_KEY = os.environ.get('BUNNY_ACCESS_KEY')
BUNNY_PULL_ZONE_URL = os.environ.get('BUNNY_PULL_ZONE_URL')
TESLA_EMAIL = os.environ.get('TESLA_EMAIL')
TESLA_REFRESH_TOKEN = os.environ.get('TESLA_REFRESH_TOKEN')
MY_CAR_NAME = "MLSII - Tesla 3"

# At the start of get_tesla_data():
logger.info(f"Environment check - TESLA_EMAIL: {'Set' if TESLA_EMAIL else 'Not Set'}")
logger.info(f"Environment check - TESLA_REFRESH_TOKEN: {'Set' if TESLA_REFRESH_TOKEN else 'Not Set'}")

# Log environment status at startup
logger.info("Environment Variables Status:")
logger.info(f"TESLA_EMAIL length: {len(TESLA_EMAIL) if TESLA_EMAIL else 0}")
logger.info(f"TESLA_REFRESH_TOKEN length: {len(TESLA_REFRESH_TOKEN) if TESLA_REFRESH_TOKEN else 0}")
logger.info(f"BUNNY_STORAGE_ZONE set: {'Yes' if BUNNY_STORAGE_ZONE else 'No'}")
logger.info(f"BUNNY_API_KEY set: {'Yes' if BUNNY_API_KEY else 'No'}")
logger.info(f"BUNNY_PULL_ZONE_URL set: {'Yes' if BUNNY_PULL_ZONE_URL else 'No'}")

def get_tesla_data():
    """Fetch Tesla vehicle data with improved error handling."""
    try:
        logger.info("Starting Tesla data fetch...")
        
        if not TESLA_EMAIL or not TESLA_REFRESH_TOKEN:
            logger.error(f"Missing credentials - Email: {bool(TESLA_EMAIL)}, Token: {bool(TESLA_REFRESH_TOKEN)}")
            return None
        
        logger.info("Creating Tesla instance...")
        with teslapy.Tesla(TESLA_EMAIL) as tesla:
            # Set the refresh token directly
            tesla.refresh_token = TESLA_REFRESH_TOKEN
            
            try:
                logger.info("Fetching token...")
                tesla.fetch_token()
                logger.info("Token fetch successful")
            except Exception as e:
                logger.error(f"Token fetch failed: {str(e)}")
                return None

            logger.info("Getting vehicle list...")
            vehicles = tesla.vehicle_list()
            
            if not vehicles:
                logger.error("No vehicles found")
                return None

            # Find specific car
            my_car = None
            for v in vehicles:
                logger.info(f"Found vehicle: {v['display_name']}")
                if v['display_name'] == MY_CAR_NAME:
                    my_car = v
                    break

            if not my_car:
                logger.error(f"Could not find car named {MY_CAR_NAME}")
                return None

            current_state = my_car['state']
            logger.info(f"Car state: {current_state}")

            if current_state == 'online':
                try:
                    data = my_car.get_vehicle_data()
                    charge_state = data['charge_state']
                    return {
                        'battery_level': charge_state['battery_level'],
                        'range': int(charge_state['battery_range']),
                        'state': 'online'
                    }
                except Exception as e:
                    logger.error(f"Failed to get vehicle data: {str(e)}")
                    return {'state': current_state}
            else:
                return {'state': current_state}

    except Exception as e:
        logger.error(f"Tesla API Error: {str(e)}")
        logger.exception("Full traceback:")
        return None

def get_media_from_bunny():
    """Fetch media files from BunnyCDN."""
    if not all([BUNNY_STORAGE_ZONE, BUNNY_API_KEY, BUNNY_PULL_ZONE_URL]):
        logger.error("Bunny CDN credentials not configured")
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
        logger.error(f"Error: {str(e)}")
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