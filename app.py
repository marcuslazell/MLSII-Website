import os
from flask import Flask, render_template, request, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Update the upload folder path to match new structure
UPLOAD_FOLDER = 'static/portfolio'  # Changed from 'static/images/portfolio'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_type(filename):
    ext = filename.rsplit('.', 1)[1].lower()
    return 'video' if ext == 'mp4' else 'image'

def get_portfolio_items():
    portfolio_path = os.path.join(app.static_folder, 'portfolio')  # Changed from 'images/portfolio'
    if not os.path.exists(portfolio_path):
        os.makedirs(portfolio_path)
    
    items = []
    for filename in os.listdir(portfolio_path):
        if allowed_file(filename):
            items.append({
                'url': url_for('static', filename=f'portfolio/{filename}'),  # Changed from 'images/portfolio/{filename}'
                'description': filename.split('.')[0],
                'type': get_file_type(filename)
            })
    return items

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/photography')
def photography():
    portfolio_items = get_portfolio_items()
    return render_template('photography.html', portfolio_items=portfolio_items)

@app.route('/tesla')
def tesla():
    return render_template('tesla.html')

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
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return 'File uploaded successfully'

if __name__ == '__main__':
    app.run(debug=True)