import os
import requests
from dataclasses import dataclass
from typing import List
from flask import Flask, render_template
from dotenv import load_dotenv

# Initialize Flask and load environment variables
app = Flask(__name__)
load_dotenv()

@dataclass
class MediaItem:
    """Data structure for media items (images/videos)"""
    filename: str
    url: str
    type: str
    description: str

class BunnyManager:
    """Handles all Bunny.net CDN interactions"""
    def __init__(self):
        # Note: Storage zone name must exactly match Bunny.net username
        self.storage_zone = "mlsii-website"  # Fixed the name to match Bunny.net
        self.access_key = os.getenv('BUNNY_ACCESS_KEY')
        self.pull_zone = os.getenv('BUNNY_PULLZONE_URL')
        
        print("\n=== Bunny.net Configuration ===")
        print(f"Storage Zone: {self.storage_zone}")
        print(f"Pull Zone: {self.pull_zone}")
        print(f"Access Key (first 10 chars): {self.access_key[:10] if self.access_key else 'None'}")
    
    def get_media_type(self, filename: str) -> str:
        """Determine if file is video or image based on extension"""
        return 'video' if filename.lower().endswith('.mp4') else 'image'
    
    def get_description(self, filename: str) -> str:
        """Generate a readable description from filename"""
        base = filename.rsplit('.', 1)[0]
        return base.replace('_', ' ').replace('-', ' ').title()
    
    def get_cdn_url(self, filename: str) -> str:
        """Generate CDN URL for a file"""
        return f"{self.pull_zone}/{filename}"
    
    def list_media(self) -> List[MediaItem]:
        """Fetch all media files from storage"""
        try:
            url = f"https://la.storage.bunnycdn.com/{self.storage_zone}/"
            headers = {
                'AccessKey': self.access_key,
                'Accept': 'application/json'
            }
            
            print("\n=== Making Request ===")
            print(f"URL: {url}")
            print(f"Headers: {headers}")
            
            response = requests.get(url, headers=headers)
            
            print("\n=== Response ===")
            print(f"Status: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            print(f"Content: {response.text[:200]}")
            
            if response.status_code == 401:
                print("\n!!! Authentication Error !!!")
                print("Please verify:")
                print("1. Storage Zone name is correct (check for typos)")
                print("2. Access Key is correct and not expired")
                print("3. Access Key has appropriate permissions")
                return []
            
            response.raise_for_status()
            files = response.json()
            
            media_items = []
            for file in files:
                filename = file['ObjectName']
                if not filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.mp4')):
                    continue
                    
                media_items.append(MediaItem(
                    filename=filename,
                    url=self.get_cdn_url(filename),
                    type=self.get_media_type(filename),
                    description=self.get_description(filename)
                ))
                print(f"Added: {filename}")
            
            return sorted(media_items, key=lambda x: x.filename)
            
        except Exception as e:
            app.logger.error(f"Error fetching media: {str(e)}")
            print(f"\n=== Error ===\n{str(e)}")
            return []

# Initialize Bunny.net manager
bunny = BunnyManager()

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/photography')
def photography():
    """Photography portfolio page"""
    media_items = bunny.list_media()
    return render_template('photography.html', portfolio_items=media_items)

@app.route('/tesla')
def tesla():
    """Tesla page - placeholder for now"""
    return render_template('tesla.html')

@app.route('/links')
def links():
    """Links/referral page"""
    return render_template('links.html')

if __name__ == '__main__':
    app.run(debug=True)