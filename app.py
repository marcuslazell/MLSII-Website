import os
import requests
from flask import Flask, render_template
from urllib.parse import quote
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

BUNNY_STORAGE_ZONE = os.getenv('BUNNY_STORAGE_ZONE')
BUNNY_API_KEY = os.getenv('BUNNY_ACCESS_KEY')
BUNNY_PULL_ZONE_URL = "https://mlsiiwebsite.b-cdn.net"

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