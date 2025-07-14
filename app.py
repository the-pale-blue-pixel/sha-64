import os
import threading
import requests
from flask import Flask, request, jsonify, render_template, send_file
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

app = Flask(__name__)

STATIC_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
GENERATED_IMAGE_PATH = os.path.join(STATIC_FOLDER, 'generated', 'image.png')
FONT_PATH = os.path.join(STATIC_FOLDER, 'fonts', 'Pixel Operator Mono 8 Regular_23949.ttf')

image_generation_lock = threading.Lock()

# PONER ACÁ LA DIRECCIÓN DE AFIRME !!!!! 
IMPRESORA_ENDPOINT = "http://192.168.1.100:5000/print_image"

def enviar_a_impresora(image_path):
    """Envía la imagen al endpoint remoto de la impresora."""
    try:
        with open(image_path, 'rb') as img_file:
            files = {'file': ('image.png', img_file, 'image/png')}
            response = requests.post(IMPRESORA_ENDPOINT, files=files)
        if response.status_code == 200:
            print("✅ Imagen enviada a la impresora con éxito.")
        else:
            print(f"❌ Error al enviar a impresora. Código: {response.status_code}")
    except Exception as e:
        print("❌ Excepción al enviar a impresora:", e)

def crear_imagen(password_texto):
    """Genera una imagen con los datos y guarda en disco."""
    try:
        font_large = ImageFont.truetype(FONT_PATH, 25)
        font = ImageFont.truetype(FONT_PATH, 14)
        font_small = ImageFont.truetype(FONT_PATH, 10)
    except Exception as e:
        print("Error al cargar fuente:", e)
        font_large = font = font_small = ImageFont.load_default()

    img_width = 600
    line_spacing = 8
    y = 20

    lines = [
        ("*" * 53, font_small, "center"),
        (password_texto, font_large, "center"),
        ("*" * 53, font_small, "center"),
        ("", None, "spacer"),
        ("type: transaction", font, "center"),
        ("", None, "divider"),
        (("id:", "xxxxxxxxx"), font, "row"),
        (("entrypoint:", "mint"), font, "row"),
        (("status:", "applied"), font, "row"),
        (("counter:", "xxxxxxx"), font, "row"),
        (("level:", "xxxxxxx"), font, "row"),
        ("", None, "divider"),
        ("Timestamp:", font, "left"),
        (datetime.now().isoformat(), font, "left"),
        ("", None, "divider"),
        ("HASH", font, "center"),
        (' '.join(['xxxxxxxxx'] * 4), font_small, "center"),
        (' '.join(['xxxxxxxxx'] * 4), font_small, "center"),
    ]

    def calc_height():
        total = y
        for text, f, kind in lines:
            if kind in ["divider", "spacer"]:
                total += 10
            else:
                h = f.getbbox("Ag")[3] if f else 20
                total += h + line_spacing
        return total + 20

    img_height = calc_height()
    img = Image.new("RGB", (img_width, img_height), "white")
    draw = ImageDraw.Draw(img)

    for text, f, align in lines:
        if align == "spacer":
            y += 10
            continue
        if align == "divider":
            draw.line([(20, y), (img_width - 20, y)], fill="black", width=1)
            y += 10
            continue
        if align == "row":
            left_text, right_text = text
            left_w = draw.textlength(left_text, font=f)
            right_w = draw.textlength(right_text, font=f)
            left_x = 40
            right_x = img_width - 40 - right_w
            draw.text((left_x, y), left_text, fill="black", font=f)
            draw.text((right_x, y), right_text, fill="black", font=f)
            y += f.getbbox("Ag")[3] + line_spacing
            continue

        w = draw.textlength(text, font=f) if f else 0
        if align == "left":
            x = 40
        elif align == "right":
            x = img_width - 40 - w
        elif align == "center":
            x = (img_width - w) / 2
        else:
            x = 0
        draw.text((x, y), text, fill="black", font=f)
        y += f.getbbox("Ag")[3] + line_spacing if f else 20

    os.makedirs(os.path.dirname(GENERATED_IMAGE_PATH), exist_ok=True)
    try:
        img.save(GENERATED_IMAGE_PATH)
        print("✅ Imagen generada:", GENERATED_IMAGE_PATH)
    except Exception as e:
        print("❌ Error al guardar imagen:", e)

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
        # 👇 Enviar en un hilo separado para no bloquear la respuesta
        threading.Thread(target=enviar_a_impresora, args=(GENERATED_IMAGE_PATH,)).start()

    process()
    return jsonify({ "image_url": "/print" })

@app.route('/print')
def print_image():
    return send_file(GENERATED_IMAGE_PATH, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)

