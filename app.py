import os
import requests
from flask import Flask, render_template
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

BUNNY_STORAGE_ZONE = os.getenv('BUNNY_STORAGE_ZONE')
BUNNY_API_KEY = os.getenv('BUNNY_ACCESS_KEY')
BUNNY_PULL_ZONE_URL = os.getenv('BUNNY_PULL_ZONE_URL')

def get_media_from_bunny():
    url = f"https://la.storage.bunnycdn.com/{BUNNY_STORAGE_ZONE}/"
    headers = {"AccessKey": BUNNY_API_KEY}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        files = response.json()
        
        media = [
            {
                "url": f"{BUNNY_PULL_ZONE_URL}/{file['ObjectName']}", 
                "description": file['ObjectName'].split('.')[0],
                "type": "video" if file['ObjectName'].lower().endswith('.mp4') else "image"
            }
            for file in files
            if not file.get('IsDirectory') and 
            file['ObjectName'].lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.mp4'))
        ]
        return media
    except requests.exceptions.RequestException as e:
        print(f"Error fetching media from Bunny.net: {e}")
        return []

@app.route('/photography')
def photography():
    portfolio_items = get_media_from_bunny()
    return render_template("photography.html", portfolio_items=portfolio_items)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/tesla')
def tesla():
    return render_template('tesla.html')

@app.route('/links')
def links():
    return render_template('links.html')

if __name__ == '__main__':
    app.run(debug=True)