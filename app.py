import os
import requests
from flask import Flask, render_template
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import List

# Initialize Flask and load environment variables
app = Flask(__name__)
load_dotenv()

BUNNY_STORAGE_ZONE = os.getenv('BUNNY_STORAGE_ZONE')
BUNNY_API_KEY = os.getenv('BUNNY_ACCESS_KEY')
BUNNY_PULL_ZONE_URL = os.getenv('BUNNY_PULL_ZONE_URL')

def get_images_from_bunny():
    """Fetches image data from Bunny.net storage."""
    url = f"https://la.storage.bunnycdn.com/{BUNNY_STORAGE_ZONE}/"
    headers = {"AccessKey": BUNNY_API_KEY}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        files = response.json()
        images = [
            {"url": f"{BUNNY_PULL_ZONE_URL}/{file['ObjectName']}", "description": file['ObjectName']}
            for file in files
            if not file.get('IsDirectory') and file['ObjectName'].lower().endswith(('.jpg', '.png', '.jpeg'))
        ]
        return images
    except requests.exceptions.RequestException as e:
        print(f"Error fetching images from Bunny.net: {e}")
        return []


@app.route('/photography')
def photography():
    # BunnyCDN Storage API Details
    storage_zone_name = "mlsii-website"
    access_key = os.getenv("BUNNY_ACCESS_KEY")
    storage_url = f"https://la.storage.bunnycdn.com/{storage_zone_name}/"

    # Make a GET request to fetch file data
    headers = {"AccessKey": access_key}
    response = requests.get(storage_url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        files = response.json()
        portfolio_items = [
            {"url": f"{storage_url}{file['ObjectName']}", "description": file['ObjectName']}
            for file in files
        ]
    else:
        # If the request fails, return an error message or a fallback page
        portfolio_items = []
        print(f"Error fetching files: {response.status_code} - {response.text}")

    return render_template("photography.html", portfolio_items=portfolio_items)

@app.route('/')
def index():
    """Render the home page."""
    return render_template('index.html')


@app.route('/tesla')
def tesla():
    """Render the Tesla project page."""
    return render_template('tesla.html')


@app.route('/links')
def links():
    """Render the links/referral page."""
    return render_template('links.html')


if __name__ == '__main__':
    app.run(debug=True)