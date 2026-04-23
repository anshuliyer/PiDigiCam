import os
from flask import Flask, render_template, send_from_directory, request, redirect, url_for

app = Flask(__name__)

# Config
PHOTO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../Captured"))

@app.route('/')
def index():
    if not os.path.exists(PHOTO_DIR):
        os.makedirs(PHOTO_DIR, exist_ok=True)
    
    files = sorted([f for f in os.listdir(PHOTO_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png'))], reverse=True)
    return render_template('index.html', images=files)

@app.route('/images/<filename>')
def get_image(filename):
    return send_from_directory(PHOTO_DIR, filename)

@app.route('/download/<filename>')
def download_image(filename):
    return send_from_directory(PHOTO_DIR, filename, as_attachment=True)

@app.route('/delete/<filename>', methods=['POST'])
def delete_image(filename):
    img_path = os.path.join(PHOTO_DIR, filename)
    if os.path.exists(img_path):
        os.remove(img_path)
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Run server on all interfaces so it's accessible over network
    app.run(host='0.0.0.0', port=5000, debug=False)
