"""
Export des visualisations thermiques en images PNG.
Reproduit exactement les couleurs du terminal (ANSI 256).
Inclut: barre de couleur, températures par pièce, timestamp.
"""

from PIL import Image, ImageDraw, ImageFont


# Palette ANSI 256 couleurs -> RGB
# https://www.ditig.com/publications/256-colors-cheat-sheet
ANSI_256_TO_RGB = {
    16: (0, 0, 0),        # Noir (murs)
    21: (0, 0, 255),      # Bleu (capteur IAQ)
    46: (0, 255, 0),      # Vert (actionneur)
    57: (95, 0, 175),     # Violet foncé (extérieur)
    196: (255, 0, 0),     # Rouge vif (capteur temp / très chaud)
    # Cyan range (51-61) pour 10-15°C
    51: (0, 255, 255),
    52: (95, 0, 0),
    53: (95, 0, 95),
    54: (95, 0, 135),
    55: (95, 0, 175),
    56: (95, 0, 215),
    58: (95, 95, 0),
    59: (95, 95, 95),
    60: (95, 95, 135),
    61: (95, 95, 175),
    # Jaune range (220-226) pour 15-20°C
    220: (255, 215, 0),
    221: (255, 215, 95),
    222: (255, 215, 135),
    223: (255, 215, 175),
    224: (255, 215, 215),
    225: (255, 215, 255),
    226: (255, 255, 0),
    # Orange range (208-216) pour 20-25°C
    208: (255, 135, 0),
    209: (255, 135, 95),
    210: (255, 135, 135),
    211: (255, 135, 175),
    212: (255, 135, 215),
    213: (255, 135, 255),
    214: (255, 175, 0),
    215: (255, 175, 95),
    216: (255, 175, 135),
    # Rouge range (196-200) pour 25-30°C
    197: (255, 0, 95),
    198: (255, 0, 135),
    199: (255, 0, 175),
    200: (255, 0, 215),
}

# Dimensions des éléments additionnels
COLORBAR_WIDTH = 30
COLORBAR_MARGIN = 20
INFO_PANEL_HEIGHT = 120
PADDING = 10


def ansi_code_to_rgb(code):
    """
    Convertit un code ANSI 256 en RGB.
    Utilise la table de correspondance standard.
    """
    if code in ANSI_256_TO_RGB:
        return ANSI_256_TO_RGB[code]
    
    # Calcul générique pour les codes 16-231 (cube 6x6x6)
    if 16 <= code <= 231:
        code -= 16
        r = (code // 36) * 51
        g = ((code // 6) % 6) * 51
        b = (code % 6) * 51
        return (r, g, b)
    
    # Grayscale (232-255)
    if 232 <= code <= 255:
        gray = (code - 232) * 10 + 8
        return (gray, gray, gray)
    
    return (128, 128, 128)


def get_color_rgb_temp(temp):
    """
    Retourne la couleur RGB basée sur la température.
    IDENTIQUE à get_color_square_temp() dans thermal_view.py
    """
    if temp == -1:  # Mur
        return ansi_code_to_rgb(16)
    
    temp = max(10, min(30, temp))
    
    if temp < 15:  # Cyan (10-15°C)
        ratio = (temp - 10) / 5.0
        color_code = int(51 + ratio * 10)
    elif temp < 20:  # Jaune (15-20°C)
        ratio = (temp - 15) / 5.0
        color_code = int(220 + ratio * 6)
    elif temp < 25:  # Orange (20-25°C)
        ratio = (temp - 20) / 5.0
        color_code = int(208 + ratio * 8)
    else:  # Rouge (25-30°C)
        ratio = (temp - 25) / 5.0
        color_code = int(196 + ratio * 4)
    
    return ansi_code_to_rgb(color_code)


def save_thermal_image(flat, output_path, cell_size=20, timestamp=None, room_temps=None):
    """
    Sauvegarde la grille thermique en image PNG.
    Reproduit exactement l'affichage du terminal.
    
    Args:
        flat: Grille 2D de Cell objects
        output_path: Chemin de sortie (.png)
        cell_size: Taille de chaque cellule en pixels
        timestamp: Horodatage à afficher (optionnel)
        room_temps: Dict {room_name: temperature} (optionnel, sinon extrait de flat)
    """
    height = len(flat)
    width = len(flat[0]) if height > 0 else 0
    
    grid_width = width * cell_size
    grid_height = height * cell_size
    
    # Dimensions totales avec colorbar et panneau d'info
    total_width = grid_width + COLORBAR_WIDTH + COLORBAR_MARGIN * 2 + 60
    total_height = grid_height + INFO_PANEL_HEIGHT + PADDING * 2
    
    img = Image.new('RGB', (total_width, total_height), color=(40, 40, 40))
    draw = ImageDraw.Draw(img)
    
    # Charger la police
    try:
        font_large = ImageFont.truetype("arial.ttf", 16)
        font_small = ImageFont.truetype("arial.ttf", 12)
        font_title = ImageFont.truetype("arial.ttf", 14)
    except:
        font_large = ImageFont.load_default()
        font_small = font_large
        font_title = font_large
    
    # === Dessiner la grille thermique ===
    grid_x_offset = PADDING
    grid_y_offset = PADDING
    
    for i in range(height):
        for j in range(width):
            cell = flat[i][j]
            x = grid_x_offset + j * cell_size
            y = grid_y_offset + i * cell_size
            
            # Mur (noir)
            if cell.is_wall and not cell.is_window:
                color = ansi_code_to_rgb(16)
            # Extérieur (violet foncé)
            elif cell.is_outside:
                color = ansi_code_to_rgb(57)
            # Capteur température (rouge avec T)
            elif cell.sensor == "SENSOR_TEMP":
                color = ansi_code_to_rgb(196)
            # Capteur IAQ (bleu avec I)
            elif cell.sensor == "SENSOR_IAQ":
                color = ansi_code_to_rgb(21)
            # Actionneur (vert avec H)
            elif cell.actuator:
                color = ansi_code_to_rgb(46)
            # Température normale
            else:
                color = get_color_rgb_temp(cell.temp)
            
            draw.rectangle(
                [x, y, x + cell_size - 1, y + cell_size - 1],
                fill=color
            )
            
            # Ajouter les lettres pour les capteurs/actionneurs
            if cell.sensor == "SENSOR_TEMP":
                _draw_letter(draw, x, y, cell_size, "T", (255, 255, 255))
            elif cell.sensor == "SENSOR_IAQ":
                _draw_letter(draw, x, y, cell_size, "I", (255, 255, 255))
            elif cell.actuator:
                _draw_letter(draw, x, y, cell_size, "A", (0, 0, 0))
    
    # === Dessiner la barre de couleur (colorbar) ===
    colorbar_x = grid_x_offset + grid_width + COLORBAR_MARGIN
    colorbar_y = grid_y_offset
    colorbar_height = grid_height
    
    _draw_colorbar(draw, colorbar_x, colorbar_y, COLORBAR_WIDTH, colorbar_height, font_small)
    
    # === Extraire les températures par pièce si non fournies ===
    if room_temps is None:
        room_temps = _extract_room_temps(flat)
    
    # === Panneau d'information en bas ===
    info_y = grid_y_offset + grid_height + PADDING
    
    if timestamp:
        draw.text(
            (PADDING, info_y),
            f"⏱ {timestamp}",
            fill=(255, 255, 255),
            font=font_large
        )
    
    # Températures par pièce
    if room_temps:
        temp_y = info_y + 25
        draw.text((PADDING, temp_y), "Températures par pièce:", fill=(200, 200, 200), font=font_title)
        
        temp_y += 20
        col_width = 180
        col = 0
        
        for room in sorted(room_temps.keys()):
            temp = room_temps[room]
            color = get_color_rgb_temp(temp)
            
            x_pos = PADDING + (col % 3) * col_width
            y_pos = temp_y + (col // 3) * 18
            
            # Carré de couleur
            draw.rectangle([x_pos, y_pos, x_pos + 12, y_pos + 12], fill=color)
            
            # Texte
            draw.text(
                (x_pos + 16, y_pos - 2),
                f"{room}: {temp:.1f}°C",
                fill=(255, 255, 255),
                font=font_small
            )
            col += 1
    
    img.save(output_path)
    print(f"  [OK] {output_path}")


def _draw_colorbar(draw, x, y, width, height, font):
    """
    Dessine une barre de couleur verticale (10°C en bas -> 30°C en haut).
    """
    # Dessiner le gradient
    for i in range(height):
        # Température de 30°C (haut) à 10°C (bas)
        temp = 30 - (i / height) * 20
        color = get_color_rgb_temp(temp)
        draw.line([(x, y + i), (x + width, y + i)], fill=color)
    
    # Bordure
    draw.rectangle([x - 1, y - 1, x + width + 1, y + height + 1], outline=(100, 100, 100))
    
    # Labels de température
    labels = [30, 25, 20, 15, 10]
    for temp in labels:
        label_y = y + int((30 - temp) / 20 * height)
        draw.text((x + width + 5, label_y - 6), f"{temp}°C", fill=(200, 200, 200), font=font)


def _extract_room_temps(flat):
    """
    Extrait les températures par pièce depuis la grille.
    """
    room_temps = {}
    for row in flat:
        for cell in row:
            if cell.sensor == "SENSOR_TEMP" and cell.room:
                room_temps[cell.room] = cell.temp
    return room_temps


def _draw_letter(draw, x, y, cell_size, letter, color):
    """Dessine une lettre centrée dans la cellule."""
    try:
        font = ImageFont.truetype("arial.ttf", cell_size // 2)
    except:
        font = ImageFont.load_default()
    
    # Centrer la lettre
    bbox = draw.textbbox((0, 0), letter, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    text_x = x + (cell_size - text_width) // 2
    text_y = y + (cell_size - text_height) // 2
    
    draw.text((text_x, text_y), letter, fill=color, font=font)
