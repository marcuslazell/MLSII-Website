import os
from dataclasses import dataclass
from typing import List, Optional
import json
from flask import Flask, render_template, request, url_for, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from functools import wraps
# Removing tesla_api import temporarily

# Initialize Flask and load environment variables
app = Flask(__name__)
load_dotenv()

# Configuration
UPLOAD_FOLDER = 'static/portfolio'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Portfolio data structures
@dataclass
class PortfolioItem:
    filename: str
    description: str
    type: str
    bunny_url: str

class BunnyConfig:
    def __init__(self):
        self.pull_zone_url = os.getenv('BUNNY_PULLZONE_URL', 'https://your-pullzone.b-cdn.net')
        self.storage_zone_url = os.getenv('BUNNY_STORAGE_URL', 'https://storage.bunnycdn.com')
        self.storage_zone = os.getenv('BUNNY_STORAGE_ZONE')
        self.access_key = os.getenv('BUNNY_ACCESS_KEY')
        
    @property
    def is_configured(self) -> bool:
        return all([self.pull_zone_url, self.storage_zone, self.access_key])

class PortfolioManager:
    def __init__(self, app):
        self.app = app
        self.bunny_config = BunnyConfig()
        self.portfolio_data_path = os.path.join(app.static_folder, 'portfolio_data.json')
        
    def get_bunny_url(self, filename: str) -> str:
        return f"{self.bunny_config.pull_zone_url}/portfolio/{filename}"
    
    def get_file_type(self, filename: str) -> str:
        ext = filename.rsplit('.', 1)[1].lower()
        return 'video' if ext == 'mp4' else 'image'
    
    def load_portfolio_data(self) -> List[PortfolioItem]:
        if not os.path.exists(self.portfolio_data_path):
            return []
            
        try:
            with open(self.portfolio_data_path, 'r') as f:
                data = json.load(f)
                return [PortfolioItem(**item) for item in data]
        except Exception as e:
            self.app.logger.error(f"Error loading portfolio data: {e}")
            return []
    
    def save_portfolio_data(self, items: List[PortfolioItem]):
        try:
            with open(self.portfolio_data_path, 'w') as f:
                json.dump([vars(item) for item in items], f, indent=2)
        except Exception as e:
            self.app.logger.error(f"Error saving portfolio data: {e}")
    
    def add_portfolio_item(self, filename: str, description: Optional[str] = None) -> PortfolioItem:
        items = self.load_portfolio_data()
        
        new_item = PortfolioItem(
            filename=filename,
            description=description or filename.split('.')[0],
            type=self.get_file_type(filename),
            bunny_url=self.get_bunny_url(filename)
        )
        
        items.append(new_item)
        self.save_portfolio_data(items)
        return new_item

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize PortfolioManager
portfolio_manager = PortfolioManager(app)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/photography')
def photography():
    portfolio_items = portfolio_manager.load_portfolio_data()
    return render_template('photography.html', portfolio_items=portfolio_items)

@app.route('/tesla')
def tesla():
    # Temporarily returning a simple template without Tesla API functionality
    return render_template('tesla.html')

@app.route('/api/tesla/status', methods=['GET'])
def get_tesla_status():
    # Temporarily returning mock data
    mock_data = {
        'battery_level': 75,
        'charging_state': 'Disconnected',
        'range': 250
    }
    return jsonify(mock_data)

@app.route('/links')
def links():
    return render_template('links.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part'
        
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        
        # Save locally if Bunny.net is not configured
        if not portfolio_manager.bunny_config.is_configured:
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
        # TODO: Add Bunny.net upload logic here using their API
        
        portfolio_manager.add_portfolio_item(filename)
        return 'File uploaded successfully'
        
    return 'Invalid file type'

if __name__ == '__main__':
    app.run(debug=True)