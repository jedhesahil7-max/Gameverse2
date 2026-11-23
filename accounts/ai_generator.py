import os
import uuid
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from django.conf import settings

THEMES = {
    "cyan": {
        "primary": (0, 229, 255),
        "secondary": (0, 150, 200),
        "dark": (11, 15, 25),
        "accent": (255, 255, 255),
        "glow": (0, 229, 255, 60),
    },
    "purple": {
        "primary": (139, 92, 246),
        "secondary": (109, 40, 217),
        "dark": (14, 11, 28),
        "accent": (230, 210, 255),
        "glow": (139, 92, 246, 60),
    },
    "gold": {
        "primary": (245, 158, 11),
        "secondary": (217, 119, 6),
        "dark": (26, 20, 10),
        "accent": (254, 243, 199),
        "glow": (245, 158, 11, 60),
    },
    "red": {
        "primary": (239, 68, 68),
        "secondary": (185, 28, 28),
        "dark": (28, 11, 11),
        "accent": (254, 202, 202),
        "glow": (239, 68, 68, 60),
    },
    "green": {
        "primary": (16, 185, 129),
        "secondary": (5, 150, 105),
        "dark": (10, 26, 18),
        "accent": (209, 250, 229),
        "glow": (16, 185, 129, 60),
    },
}

ICONS = ["wolf", "dragon", "crown", "skull", "lightning", "swords", "vanguard", "falcon"]


def draw_shield(draw, center_x, center_y, width, height, fill_color, outline_color, line_width=4):
    """Draws a sleek angular esports crest shield polygon."""
    hw = width / 2
    hh = height / 2
    top = center_y - hh
    bottom = center_y + hh
    left = center_x - hw
    right = center_x + hw

    # Angular esports shield points
    points = [
        (left + 20, top),
        (right - 20, top),
        (right, top + 25),
        (right, center_y + hh * 0.3),
        (center_x + hw * 0.5, center_y + hh * 0.7),
        (center_x, bottom),
        (center_x - hw * 0.5, center_y + hh * 0.7),
        (left, center_y + hh * 0.3),
        (left, top + 25),
    ]

    draw.polygon(points, fill=fill_color, outline=outline_color, width=line_width)
    return points


def draw_mascot(draw, cx, cy, mascot_type, primary, accent):
    """Draws geometric stylized esports mascot insignia."""
    if mascot_type == "wolf":
        # Angular Wolf Head
        pts_face = [(cx, cy + 50), (cx - 45, cy), (cx - 30, cy - 40), (cx - 50, cy - 70), 
                    (cx - 20, cy - 50), (cx, cy - 70), (cx + 20, cy - 50), (cx + 50, cy - 70), 
                    (cx + 30, cy - 40), (cx + 45, cy)]
        draw.polygon(pts_face, fill=primary, outline=accent, width=3)
        # Eyes
        draw.polygon([(cx - 25, cy - 15), (cx - 10, cy - 15), (cx - 18, cy - 25)], fill=accent)
        draw.polygon([(cx + 25, cy - 15), (cx + 10, cy - 15), (cx + 18, cy - 25)], fill=accent)
        # Snout
        draw.polygon([(cx, cy + 25), (cx - 12, cy + 5), (cx + 12, cy + 5)], fill=(15, 23, 42))

    elif mascot_type == "dragon":
        # Dragon Crest
        draw.polygon([(cx, cy - 75), (cx - 35, cy - 20), (cx - 55, cy + 10), (cx - 20, cy + 15),
                      (cx, cy + 60), (cx + 20, cy + 15), (cx + 55, cy + 10), (cx + 35, cy - 20)],
                     fill=primary, outline=accent, width=3)
        # Horns
        draw.line([(cx - 25, cy - 35), (cx - 55, cy - 65)], fill=accent, width=4)
        draw.line([(cx + 25, cy - 35), (cx + 55, cy - 65)], fill=accent, width=4)
        # Eyes
        draw.polygon([(cx - 20, cy - 5), (cx - 8, cy - 8), (cx - 14, cy - 18)], fill=accent)
        draw.polygon([(cx + 20, cy - 5), (cx + 8, cy - 8), (cx + 14, cy - 18)], fill=accent)

    elif mascot_type == "crown":
        # Royal Crown
        pts = [(cx - 55, cy + 30), (cx - 65, cy - 30), (cx - 30, cy - 5), (cx, cy - 65),
               (cx + 30, cy - 5), (cx + 65, cy - 30), (cx + 55, cy + 30)]
        draw.polygon(pts, fill=primary, outline=accent, width=3)
        draw.ellipse([cx - 10, cy - 75, cx + 10, cy - 55], fill=accent)
        draw.ellipse([cx - 72, cy - 40, cx - 58, cy - 26], fill=accent)
        draw.ellipse([cx + 58, cy - 40, cx + 72, cy - 26], fill=accent)
        # Crown jewels
        draw.rectangle([cx - 40, cy + 10, cx + 40, cy + 22], fill=accent)

    elif mascot_type == "swords":
        # Crossed Esports Blades
        # Blade 1
        draw.polygon([(cx - 55, cy - 55), (cx + 55, cy + 55), (cx + 45, cy + 65), (cx - 65, cy - 45)], fill=accent)
        # Blade 2
        draw.polygon([(cx + 55, cy - 55), (cx - 55, cy + 55), (cx - 45, cy + 65), (cx + 65, cy - 45)], fill=primary)
        # Center Diamond
        draw.polygon([(cx, cy - 20), (cx + 20, cy), (cx, cy + 20), (cx - 20, cy)], fill=(255, 255, 255), outline=primary, width=2)

    elif mascot_type == "lightning":
        # Dynamic Bolt
        pts = [(cx + 15, cy - 70), (cx - 35, cy - 5), (cx - 5, cy - 5), (cx - 20, cy + 70),
               (cx + 35, cy + 5), (cx + 5, cy + 5)]
        draw.polygon(pts, fill=primary, outline=accent, width=3)

    else:
        # Vanguard / Shield / Star Emblem
        draw.polygon([(cx, cy - 65), (cx + 45, cy), (cx, cy + 65), (cx - 45, cy)], fill=primary, outline=accent, width=3)
        draw.polygon([(cx, cy - 35), (cx + 25, cy), (cx, cy + 35), (cx - 25, cy)], fill=accent)


def generate_esports_crest(team_name="SQUAD", theme_name="cyan", mascot_type="wolf", prompt=""):
    """
    Generates a 512x512 high-resolution esports clan crest.
    Saves to media/teams/ and returns the relative path.
    """
    # Detect theme from prompt keywords if supplied
    prompt_lower = (prompt or "").lower()
    if "gold" in prompt_lower or "yellow" in prompt_lower or "crown" in prompt_lower:
        theme_name = "gold"
        mascot_type = "crown"
    elif "purple" in prompt_lower or "shadow" in prompt_lower or "phantom" in prompt_lower or "void" in prompt_lower:
        theme_name = "purple"
        mascot_type = "dragon"
    elif "red" in prompt_lower or "crimson" in prompt_lower or "fire" in prompt_lower or "blood" in prompt_lower:
        theme_name = "red"
        mascot_type = "wolf"
    elif "green" in prompt_lower or "emerald" in prompt_lower or "toxic" in prompt_lower or "viper" in prompt_lower:
        theme_name = "green"
        mascot_type = "swords"
    elif "wolf" in prompt_lower:
        mascot_type = "wolf"
    elif "dragon" in prompt_lower:
        mascot_type = "dragon"
    elif "sword" in prompt_lower or "blade" in prompt_lower:
        mascot_type = "swords"
    elif "lightning" in prompt_lower or "thunder" in prompt_lower:
        mascot_type = "lightning"

    theme = THEMES.get(theme_name, THEMES["cyan"])
    img_size = 512
    img = Image.new("RGBA", (img_size, img_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx = img_size // 2
    cy = img_size // 2 - 20

    # 1. Subtle Outer Glow
    for offset in range(12, 0, -3):
        draw_shield(draw, cx, cy, 380 + offset * 2, 420 + offset * 2, None, theme["primary"] + (30,), line_width=2)

    # 2. Outer Shield
    draw_shield(draw, cx, cy, 380, 420, theme["dark"], theme["primary"], line_width=6)

    # 3. Inner Angular Border
    draw_shield(draw, cx, cy, 340, 380, None, theme["secondary"], line_width=2)

    # 4. Diagonal Esports Accent Cuts
    draw.line([(cx - 150, cy - 100), (cx - 90, cy - 100)], fill=theme["primary"], width=4)
    draw.line([(cx + 90, cy - 100), (cx + 150, cy - 100)], fill=theme["primary"], width=4)

    # 5. Draw Selected Mascot / Emblem
    draw_mascot(draw, cx, cy, mascot_type, theme["primary"], theme["accent"])

    # 6. Monogram / Clan Name Ribbon
    ribbon_y = cy + 155
    draw.polygon([
        (cx - 140, ribbon_y - 20),
        (cx + 140, ribbon_y - 20),
        (cx + 155, ribbon_y),
        (cx + 140, ribbon_y + 20),
        (cx - 140, ribbon_y + 20),
        (cx - 155, ribbon_y)
    ], fill=theme["primary"], outline=theme["accent"], width=2)

    # Text monogram
    clean_name = "".join(ch for ch in (team_name or "SQUAD") if ch.isalnum() or ch in (" ", "_", "-")).upper()
    display_text = clean_name[:12] if len(clean_name) <= 12 else clean_name[:10] + ".."

    try:
        font = ImageFont.truetype("arial.ttf", 22)
    except Exception:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), display_text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    draw.text((cx - text_w // 2, ribbon_y - text_h // 2 - 2), display_text, fill=(11, 15, 25), font=font)

    # 7. Save to Media
    output_dir = Path(settings.MEDIA_ROOT) / "teams"
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"ai_crest_{uuid.uuid4().hex[:10]}.png"
    filepath = output_dir / filename
    img.save(filepath, format="PNG")

    relative_path = f"teams/{filename}"
    media_url = f"{settings.MEDIA_URL}{relative_path}"

    return {
        "success": True,
        "filename": filename,
        "relative_path": relative_path,
        "media_url": media_url,
        "theme": theme_name,
        "mascot": mascot_type,
    }
