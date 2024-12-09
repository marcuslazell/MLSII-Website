import os
import time
import requests
from flask import Flask, render_template, request
from urllib.parse import quote
from dotenv import load_dotenv
import teslapy

app = Flask(__name__, static_folder='static')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
load_dotenv()

if app.debug:
    app.config['TEMPLATES_AUTO_RELOAD'] = True

# Environment variables
TESLA_EMAIL = os.environ.get('TESLA_EMAIL')
TESLA_REFRESH_TOKEN = os.environ.get('TESLA_REFRESH_TOKEN')
BUNNY_STORAGE_ZONE = os.environ.get('BUNNY_STORAGE_ZONE')
BUNNY_API_KEY = os.environ.get('BUNNY_ACCESS_KEY')
BUNNY_PULL_ZONE_URL = os.environ.get('BUNNY_PULL_ZONE_URL')
MY_CAR_NAME = "MLSII - Tesla 3"

def get_site_title():
    domain = request.host.split(':')[0]
    title_mapping = {
        'saintlazell.com': 'SAINTLAZELL',
        'marcuslshaw.com': 'MARCUS SHAW',
        'thesaintmarcus.com': 'THESAINTMARCUS'
    }
    return title_mapping.get(domain, 'THESAINTMARCUS')

@app.after_request
def add_header(response):
    if app.debug:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
    return response

def get_tesla_data():
    """Fetch Tesla vehicle data using Fleet API."""
    try:
        with teslapy.Tesla(TESLA_EMAIL, verify=False) as tesla:
            tesla.base_url = 'https://fleet-api.prd.na.vn.cloud.tesla.com/api/1'
            tesla.refresh_token = TESLA_REFRESH_TOKEN
            
            tesla.fetch_token()
            vehicles = tesla.vehicle_list()
            
            my_car = None
            for vehicle in vehicles:
                if vehicle['display_name'] == MY_CAR_NAME:
                    my_car = vehicle
                    break

            if not my_car:
                return {'state': 'offline'}

            current_state = my_car['state']

            if current_state == 'online':
                try:
                    data = my_car.get_vehicle_data()
                    charge_state = data['charge_state']
                    return {
                        'state': 'online',
                        'battery_level': charge_state['battery_level'],
                        'range': int(charge_state['battery_range'])
                    }
                except Exception as e:
                    return {'state': current_state}
            else:
                try:
                    my_car.sync_wake_up()
                    return {'state': 'waking_up'}
                except:
                    return {'state': current_state}

    except Exception as e:
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
    title = get_site_title()
    return render_template('index.html', title=title)

@app.route('/tesla')
def tesla():
    title = get_site_title()
    tesla_data = get_tesla_data()
    return render_template('tesla.html', tesla_data=tesla_data, title=title)

@app.route('/portfolio')
def portfolio():
    title = get_site_title()
    portfolio_items = get_media_from_bunny()
    return render_template('portfolio.html', portfolio_items=portfolio_items, title=title)

@app.route('/links')
def links():
    title = get_site_title()
    return render_template('links.html', title=title)

if __name__ == '__main__':
    app.run(debug=True)