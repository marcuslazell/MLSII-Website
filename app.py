import os
import requests
from flask import Flask, render_template
from urllib.parse import quote
from dotenv import load_dotenv
import teslapy
import time

app = Flask(__name__)
load_dotenv()

# Environment variables
BUNNY_STORAGE_ZONE = os.getenv('BUNNY_STORAGE_ZONE')
BUNNY_API_KEY = os.getenv('BUNNY_ACCESS_KEY')
BUNNY_PULL_ZONE_URL = os.getenv('BUNNY_PULL_ZONE_URL')
TESLA_EMAIL = os.getenv('TESLA_EMAIL')
MY_CAR_NAME = "MLSII - Tesla 3"  # Add your car's exact display name here

def get_tesla_data():
    try:
        print("\nAttempting to connect to Tesla API...")
        tesla = teslapy.Tesla(TESLA_EMAIL)
        tesla.fetch_token()
        
        print("Getting vehicle list...")
        vehicles = tesla.vehicle_list()
        if not vehicles:
            print("No vehicles found")
            return None

        # Find my car by name
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
        print(f"My car found! State: {current_state}")
        print(f"Full vehicle data: {my_car}")
        
        # Try to wake up the car if it's not online
        if current_state != 'online':
            print("Vehicle not online, attempting to wake...")
            try:
                my_car.sync_wake_up(timeout=60)  # Increased timeout
                print("Wake up command sent, checking new state...")
                # Re-fetch vehicle state
                vehicles = tesla.vehicle_list()
                for v in vehicles:
                    if v['display_name'] == MY_CAR_NAME:
                        my_car = v
                        break
                current_state = my_car['state']
                print(f"New state after wake attempt: {current_state}")
            except Exception as e:
                print(f"Wake up failed: {e}")
        
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
                return {'state': 'error'}
        else:
            print(f"Vehicle still not online, returning state: {current_state}")
            return {'state': current_state}
                
    except Exception as e:
        print(f"Tesla API Error: {str(e)}")
        return None

# Rest of your code stays the same...
def get_media_from_bunny():
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

@app.route('/photography')
def photography():
    portfolio_items = get_media_from_bunny()
    return render_template('photography.html', portfolio_items=portfolio_items)

@app.route('/tesla')
def tesla():
    tesla_data = get_tesla_data()
    return render_template('tesla.html', tesla_data=tesla_data)

@app.route('/links')
def links():
    return render_template('links.html')

if __name__ == '__main__':
    app.run(debug=True)