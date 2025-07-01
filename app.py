import os
import threading
from flask import Flask, request, jsonify, render_template, send_file
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)

STATIC_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
GENERATED_IMAGE_PATH = os.path.join(STATIC_FOLDER, 'generated', 'image.png')
FONT_PATH = os.path.join(STATIC_FOLDER, 'fonts', 'BIT.ttf')

image_generation_lock = threading.Lock()

def crear_imagen(password_texto):
    img_width, img_height = 600, 400
    img = Image.new('RGB', (img_width, img_height), color='white')
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(FONT_PATH, 40) if os.path.exists(FONT_PATH) else ImageFont.load_default()
    except:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), password_texto, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    spacing = 20
    total_height = 2 + spacing + text_height + spacing + 2
    start_y = (img_height - total_height) / 2

    top_y = start_y + 1
    text_y = start_y + 2 + spacing
    bottom_y = text_y + text_height + spacing + 1
    line_x1 = (img_width - text_width * 2) / 2
    line_x2 = line_x1 + text_width * 2

    draw.line([(line_x1, top_y), (line_x2, top_y)], fill='black', width=2)
    draw.text(((img_width - text_width) / 2, text_y), password_texto, fill='black', font=font)
    draw.line([(line_x1, bottom_y), (line_x2, bottom_y)], fill='black', width=2)

    os.makedirs(os.path.dirname(GENERATED_IMAGE_PATH), exist_ok=True)
    img.save(GENERATED_IMAGE_PATH)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    password = data.get("password", "")

    def process():
        with image_generation_lock:
            crear_imagen(password)

    process()
    return jsonify({ "image_url": "/print" })

@app.route('/print')
def print_image():
    return send_file(GENERATED_IMAGE_PATH, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)
