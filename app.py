from flask import Flask, request, send_file
from flask_cors import CORS
from PIL import Image
import torch
import torchvision.transforms as T
from torchvision.models.segmentation import deeplabv3_resnet101
import os
import uuid
import numpy as np

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'results'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

# AI-model laden
model = deeplabv3_resnet101(pretrained=True).eval()

# Transform voor afbeelding naar tensor
transform = T.Compose([
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225])
])

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files or 'color' not in request.form:
        return 'No image or color provided', 400

    image = request.files['image']
    color = request.form['color']
    filename = str(uuid.uuid4()) + ".png"
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    image.save(file_path)

    orig = Image.open(file_path).convert("RGB")
    img_tensor = transform(orig).unsqueeze(0)

    with torch.no_grad():
        output = model(img_tensor)['out'][0]
    seg = output.argmax(0).byte().cpu().numpy()

    # Alleen klasse 15 (gebouw/muur)
    mask = (seg == 15).astype(np.uint8) * 255

    # Kleurcode omzetten naar RGBA
    hex_color = color.lstrip("#")
    rgba = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4)) + (120,)

    # Overlay toepassen op maskergebied
    orig_rgba = orig.convert("RGBA")
    overlay = Image.new("RGBA", orig.size, rgba)
    mask_img = Image.fromarray(mask).convert("L")
    result = Image.composite(overlay, orig_rgba, mask_img)

    result_filename = f"result_{uuid.uuid4().hex}.png"
    result_path = os.path.join(RESULT_FOLDER, result_filename)
    result.save(result_path)

    return send_file(result_path, mimetype='image/png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
