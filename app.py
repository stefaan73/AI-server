from flask import Flask, request, send_file
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
from PIL import Image
import uuid

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'results'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files or 'color' not in request.form:
         return 'No image or color provided', 400
    
    image = request.files['image']
    color = request.form['color']
    filename = secure_filename(image.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    image.save(file_path)

    img = Image.open(file_path).convert("RGBA")
    overlay = Image.new("RGBA", img.size, color + "88") # 88 = transparantie
    combined = Image.alpha_composite(img, overlay)

    result_filename = f"result_{uuid.uuid4().hex}.png"
    result_path = os.path.join(RESULT_FOLDER, result_filename)
    combined.save(result_path)

    return send_file(result_path, mimetype='image/png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
