import os
import requests
from flask import Flask, render_template, request, send_from_directory
from urllib.parse import quote
from dotenv import load_dotenv

app = Flask(__name__, static_folder='static')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
load_dotenv(interpolate=False)

if app.debug:
    app.config['TEMPLATES_AUTO_RELOAD'] = True

# Environment variables
TESLA_CLIENT_ID = os.environ.get('TESLA_CLIENT_ID')
TESLA_CLIENT_SECRET = os.environ.get('TESLA_CLIENT_SECRET')
TESLA_REFRESH_TOKEN = os.environ.get('TESLA_REFRESH_TOKEN')
TESLA_FLEET_BASE_URL = os.environ.get('TESLA_FLEET_BASE_URL', 'https://fleet-api.prd.na.vn.cloud.tesla.com')
BUNNY_STORAGE_ZONE = os.environ.get('BUNNY_STORAGE_ZONE')
BUNNY_API_KEY = os.environ.get('BUNNY_ACCESS_KEY')
BUNNY_PULL_ZONE_URL = os.environ.get('BUNNY_PULL_ZONE_URL')
MY_CAR_NAME = "MLSII - Tesla 3"

@app.after_request
def add_header(response):
    if app.debug:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'

    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
    response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
    response.headers.setdefault('Permissions-Policy', 'geolocation=(), microphone=(), camera=()')
    if request.is_secure:
        response.headers.setdefault('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
    return response

def get_tesla_data():
    """Fetch Tesla vehicle status data from Fleet API using read-only requests."""
    if not TESLA_CLIENT_ID or not TESLA_REFRESH_TOKEN:
        return {'state': 'error', 'error': 'Tesla Fleet credentials are not configured'}

    try:
        token_payload = {
            'grant_type': 'refresh_token',
            'client_id': TESLA_CLIENT_ID,
            'refresh_token': TESLA_REFRESH_TOKEN
        }
        if TESLA_CLIENT_SECRET:
            token_payload['client_secret'] = TESLA_CLIENT_SECRET

        token_response = requests.post(
            'https://auth.tesla.com/oauth2/v3/token',
            data=token_payload,
            timeout=10
        )
        token_response.raise_for_status()
        access_token = token_response.json().get('access_token')
        if not access_token:
            return {'state': 'error', 'error': 'Authentication failed'}

        headers = {'Authorization': f'Bearer {access_token}'}

        vehicles_response = requests.get(
            f'{TESLA_FLEET_BASE_URL}/api/1/vehicles',
            headers=headers,
            timeout=10
        )
        vehicles_response.raise_for_status()
        vehicles = vehicles_response.json().get('response', [])
        if not vehicles:
            return {'state': 'error', 'error': 'No vehicles found'}

        my_car = next((v for v in vehicles if v.get('display_name') == MY_CAR_NAME), vehicles[0])
        state = my_car.get('state', 'unknown')
        vehicle_tag = my_car.get('id_s') or my_car.get('vehicle_id') or my_car.get('id')

        battery_level = None
        range_value = None

        # Read-only request for telemetry; no wake or control commands.
        if vehicle_tag:
            vehicle_data_response = requests.get(
                f'{TESLA_FLEET_BASE_URL}/api/1/vehicles/{vehicle_tag}/vehicle_data',
                params={'endpoints': 'charge_state;vehicle_state'},
                headers=headers,
                timeout=10
            )
            if vehicle_data_response.ok:
                vehicle_data = vehicle_data_response.json().get('response', {})
                charge_state = vehicle_data.get('charge_state', {})
                battery_level = charge_state.get('battery_level')
                range_raw = charge_state.get('battery_range')
                range_value = int(range_raw) if range_raw is not None else None

        return {
            'state': state,
            'battery_level': battery_level,
            'range': range_value
        }

    except requests.RequestException:
        return {'state': 'error', 'error': 'Could not fetch Tesla data'}

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

def get_site_title():
    domain = request.host.split(':')[0].lower()  # Convert to lowercase
    if domain.startswith('www.'):
        domain = domain[4:]  # Remove www.
    
    title_mapping = {
        'saintlazell.com': 'SAINTLAZELL',
        'marcuslshaw.com': 'MARCUS SHAW',
        'thesaintmarcus.com': 'THE SAINT MARCUS'
    }
    return title_mapping.get(domain, 'THE SAINT MARCUS')

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

@app.route('/.well-known/appspecific/com.tesla.3p.public-key.pem')
def tesla_partner_public_key():
    return send_from_directory(
        os.path.join(app.root_path, 'static', 'tesla'),
        'com.tesla.3p.public-key.pem',
        mimetype='application/x-pem-file'
    )

if __name__ == '__main__':
    app.run(debug=True)
