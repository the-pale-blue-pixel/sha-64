import os
from datetime import datetime
import random
import string
from flask import Flask, request, jsonify, render_template, send_from_directory
from PIL import Image, ImageDraw, ImageFont 

app = Flask(__name__)

# Configuración de carpetas
STATIC_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
GENERATED_FOLDER = os.path.join(STATIC_FOLDER, 'generated')
os.makedirs(GENERATED_FOLDER, exist_ok=True)

# --- CONFIGURACIÓN DE FUENTE PERSONALIZADA ---
# 1. Asegúrate de que el archivo 'BIT.ttf' esté en 'static/fonts/'
# 2. Actualiza 'CUSTOM_FONT_FILENAME' si el nombre de tu archivo es diferente
# ---------------------------------------------
CUSTOM_FONT_FILENAME = 'BIT.ttf' 
FONT_PATH = os.path.join(STATIC_FOLDER, 'fonts', CUSTOM_FONT_FILENAME)

@app.route('/')
def index():
    return render_template('index.html')

def generar_contrasena(n=10):
    """Generates a random password of n characters."""
    caracteres = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(caracteres) for _ in range(n))

def crear_imagen(password_texto):
    """
    Creates an image with the entered password, centered between two lines.
    The lines are twice the width of the password.
    This image will be saved in /static/generated but will not be displayed on the frontend.
    It attempts to use the custom font; otherwise, it falls back to Pillow's default.
    """
    img_width, img_height = 600, 400 # Size of the generated image (you can adjust)
    img = Image.new('RGB', (img_width, img_height), color='white') # Background color changed to white
    draw = ImageDraw.Draw(img)

    try:
        # Attempt to load the custom font
        if os.path.exists(FONT_PATH):
            font = ImageFont.truetype(FONT_PATH, 40) # Font size for the image (adjusted to 40 for better visibility)
        else:
            # If the custom font is not found, use Pillow's default
            app.logger.warning(f"Custom font '{CUSTOM_FONT_FILENAME}' not found at '{FONT_PATH}'. Using default font.")
            font = ImageFont.load_default()
    except IOError as e:
        app.logger.error(f"Error loading font '{CUSTOM_FONT_FILENAME}': {e}. Using default font.")
        font = ImageFont.load_default()
    except Exception as e: # Catch any other unexpected exceptions during font loading
        app.logger.error(f"Unexpected error loading font: {e}. Using default font.")
        font = ImageFont.load_default()

    # Text to be displayed on the generated image
    display_text = password_texto
    
    # Calculate text size for robust centering using textbbox
    password_bbox = draw.textbbox((0,0), display_text, font=font)
    password_text_width = password_bbox[2] - password_bbox[0]
    password_text_height = password_bbox[3] - password_bbox[1]

    # Define parameters for the lines
    line_width = password_text_width * 2
    line_thickness = 2 # Pixels for line thickness
    spacing = 20       # Vertical spacing between line and text

    # Calculate total block height for centering
    total_block_height = line_thickness + spacing + password_text_height + spacing + line_thickness

    # Calculate starting Y coordinate for the entire block (centered vertically)
    start_y = (img_height - total_block_height) / 2

    # Calculate coordinates for drawing
    
    # Top line coordinates
    top_line_x1 = (img_width - line_width) / 2
    top_line_y1 = start_y + line_thickness / 2 # Centered thickness vertically
    top_line_x2 = top_line_x1 + line_width
    top_line_y2 = top_line_y1

    # Password text coordinates
    password_x = (img_width - password_text_width) / 2
    password_y = start_y + line_thickness + spacing

    # Bottom line coordinates
    bottom_line_x1 = (img_width - line_width) / 2
    bottom_line_y1 = password_y + password_text_height + spacing + line_thickness / 2
    bottom_line_x2 = bottom_line_x1 + line_width
    bottom_line_y2 = bottom_line_y1

    # Draw the elements
    draw.line([(top_line_x1, top_line_y1), (top_line_x2, top_line_y2)], fill=(0, 0, 0), width=line_thickness) # Black line
    draw.text((password_x, password_y), display_text, fill=(0, 0, 0), font=font, align="center") # Black text
    draw.line([(bottom_line_x1, bottom_line_y1), (bottom_line_x2, bottom_line_y2)], fill=(0, 0, 0), width=line_thickness) # Black line

    # Unique filename based on date and a random number
    filename = f"generated_pass_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}.png"
    path = os.path.join(GENERATED_FOLDER, filename)
    
    try:
        img.save(path)
        app.logger.info(f"Image saved to: {path}") # Success message in the server console
    except Exception as e:
        app.logger.error(f"Error saving image to {path}: {e}")
        return "" # Returns an empty string if saving fails

    return f"/static/generated/{filename}"

@app.route('/generate', methods=['POST'])
def generar():
    try:
        data = request.get_json()
        password_ingresada = data.get("password", "") 
        
        nueva_contrasena_generada = generar_contrasena() # Generated, but not displayed on the frontend
        
        imagen_generada_url = crear_imagen(password_ingresada) # Image is created and saved
        
        return jsonify({
            "new_password": nueva_contrasena_generada, # Not displayed on the frontend
            "image_url": imagen_generada_url # Returned, but not used to display the image on the frontend
        })
    except Exception as e:
        app.logger.error(f"Error in /generate endpoint: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

# Route for serving static files (images, CSS)
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(STATIC_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)