#!/usr/bin/env python3
import os
import sys
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "pipeline" / "state"
OUT_GIF = OUT_DIR / "temp_animated.gif"
LOGO_PATH = REPO / "pipeline" / "state" / "logo.png"

# Widescreen high-fidelity V12 Agentic palette (Obsidian, Glowing Teals, and Magentas)
BG_BASE = (13, 11, 35)         # #0D0B23 Obsidian Purple-Indigo
BG_CARD = (23, 20, 54)         # #171436 Translucent Card Fill
BORDER_CARD = (58, 54, 112)     # #3A3670 Translucent Border
TEXT_WHITE = (255, 255, 255)
TEXT_MUTED = (141, 137, 190)
SAFE_TEAL = (36, 160, 169)     # #24A0A9 Teal
VIOL_PINK = (255, 0, 122)      # #FF007A Magenta
WARN_RED = (240, 72, 75)       # #F0484B Red
GLOW_YELLOW = (255, 235, 59)   # Glowing Yellow for User Position Dot

def draw_radial_gradient(draw, w, h):
    # Generates an ultra-premium centered radial glow on the canvas
    cx, cy = w // 2, h // 2
    max_r = math.sqrt(cx**2 + cy**2)
    for r in range(0, int(max_r), 8):
        factor = r / max_r
        cr = int(24 - 14 * factor)
        cg = int(20 - 12 * factor)
        cb = int(60 - 30 * factor)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(cr, cg, cb), width=8)

def draw_subtle_grid(draw, w, h):
    # Thin translucent grid overlay
    for x in range(0, w, 40):
        draw.line([(x, 0), (x, h)], fill=(28, 25, 68), width=1)
    for y in range(0, h, 40):
        draw.line([(0, y), (w, y)], fill=(28, 25, 68), width=1)

def draw_rounded_card(img, draw, x1, y1, x2, y2, r, fill, outline, width=1):
    # Renders a sleek glassmorphic container with rounded corners and border
    draw.rounded_rectangle([x1, y1, x2, y2], radius=r, fill=fill, outline=outline, width=width)

def draw_neon_dot(img, draw, cx, cy, r_dot, color):
    # Renders a multi-layer glowing particle mimicking professional motion graphics
    for r_glow in range(r_dot + 12, r_dot, -2):
        alpha_factor = (r_glow - r_dot) / 12.0
        glow_color = (
            int(color[0] + (BG_BASE[0] - color[0]) * alpha_factor),
            int(color[1] + (BG_BASE[1] - color[1]) * alpha_factor),
            int(color[2] + (BG_BASE[2] - color[2]) * alpha_factor),
        )
        draw.ellipse([cx - r_glow, cy - r_glow, cx + r_glow, cy + r_glow], fill=glow_color)
    draw.ellipse([cx - r_dot, cy - r_dot, cx + r_dot, cy + r_dot], fill=color)

def main():
    print("=== Compiling Agentic V12 Widescreen Animation (GIF) ===")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Cinematic 16:9 Landscape Layout (960x540)
    w, h = 960, 540
    frames = []
    
    # Load fonts
    try:
        font_path = "C:/Windows/Fonts/SegoeUI.ttf"
        font_large = ImageFont.truetype(font_path, 26)
        font_medium = ImageFont.truetype(font_path, 15)
        font_small = ImageFont.truetype(font_path, 12)
        font_bold = ImageFont.truetype(font_path, 18)
    except:
        font_large = font_medium = font_small = font_bold = ImageFont.load_default()

    # Load and prepare the official logo if available
    logo_img = None
    if LOGO_PATH.exists():
        try:
            raw_logo = Image.open(str(LOGO_PATH)).convert("RGBA")
            logo_img = raw_logo.resize((120, int(120 * raw_logo.height / raw_logo.width)), Image.Resampling.LANCZOS)
        except Exception as e:
            print(f"Warning: Could not resize logo: {e}")

    total_frames = 60
    
    # Mathematical Curve Points (SOL liquidation dip and recovery)
    # x ranges from 460 to 900
    # y base is 320
    def get_curve_y(x):
        # Sine-based curve that dips at 03:14 (x = 650) and recovers
        t = (x - 460) / 440.0 # 0.0 to 1.0
        if t <= 0.4:
            # Drop phase: 320 to 420
            p = t / 0.4
            return int(220 + 190 * p)
        elif 0.4 < t <= 0.5:
            # Guard activation floor (Pulsing at 410)
            return 410
        else:
            # Recovery phase: 410 to 240
            p = (t - 0.5) / 0.5
            return int(410 - (410 - 250) * p)

    for f in range(total_frames):
        # 1. Base Canvas
        img = Image.new("RGB", (w, h), BG_BASE)
        draw = ImageDraw.Draw(img)
        
        # 2. Radial Glow & Grid
        draw_radial_gradient(draw, w, h)
        draw_subtle_grid(draw, w, h)
        
        # 3. Paste Official Vanna Logo (Upper Right)
        if logo_img:
            img.paste(logo_img, (w - 160, 35), logo_img)
            
        # 4. Glassmorphic Header Panel
        draw_rounded_card(img, draw, 40, 30, 720, 115, 12, fill=BG_CARD, outline=BORDER_CARD, width=1)
        draw.text((60, 42), "VANNA RISK GUARDIAN", fill=TEXT_WHITE, font=font_large)
        draw.text((60, 78), "Policy-Bounded Autonomous Liquidation Prevention Floor  ·  Testnet", fill=TEXT_MUTED, font=font_medium)
        
        # 5. Live Audit Log (Left Panel)
        draw_rounded_card(img, draw, 40, 140, 410, 470, 14, fill=BG_CARD, outline=BORDER_CARD, width=1)
        draw.text((65, 155), "GUARDIAN REAL-TIME LOG", fill=TEXT_MUTED, font=font_bold)
        draw.line([(65, 185), (385, 185)], fill=BORDER_CARD, width=1)
        
        # Determine step activations based on frames
        ev1_on = f >= 15
        ev2_on = f >= 25
        ev3_on = f >= 45
        
        # Event 1: Drop
        col_ev1 = WARN_RED if ev1_on else TEXT_MUTED
        draw.text((65, 205), "03:14", fill=col_ev1, font=font_bold)
        draw.ellipse([(125, 212), (133, 220)], fill=(WARN_RED if ev1_on else (40, 40, 70)))
        draw.text((150, 205), "SOL dropped 12%", fill=(TEXT_WHITE if ev1_on else TEXT_MUTED), font=font_medium)
        draw.text((150, 225), "Health factor 2.4 → 1.12", fill=(WARN_RED if ev1_on else TEXT_MUTED), font=font_small)
        
        # Event 2: Guard
        col_ev2 = VIOL_PINK if ev2_on else TEXT_MUTED
        draw.text((65, 275), "03:14", fill=col_ev2, font=font_bold)
        draw.ellipse([(125, 282), (133, 290)], fill=(VIOL_PINK if ev2_on else (40, 40, 70)))
        draw.text((150, 275), "Vanna Floor Tripped", fill=(TEXT_WHITE if ev2_on else TEXT_MUTED), font=font_medium)
        draw.text((150, 295), "Debt auto-repay triggered", fill=(VIOL_PINK if ev2_on else TEXT_MUTED), font=font_small)
        
        # Event 3: Recover
        col_ev3 = SAFE_TEAL if ev3_on else TEXT_MUTED
        draw.text((65, 345), "03:15", fill=col_ev3, font=font_bold)
        draw.ellipse([(125, 352), (133, 360)], fill=(SAFE_TEAL if ev3_on else (40, 40, 70)))
        draw.text((150, 345), "Position secured", fill=(TEXT_WHITE if ev3_on else TEXT_MUTED), font=font_medium)
        draw.text((150, 365), "HF recovered to 1.62", fill=(SAFE_TEAL if ev3_on else TEXT_MUTED), font=font_small)
        
        # Bottom metrics box inside Left Panel
        draw_rounded_card(img, draw, 65, 405, 385, 455, 6, fill=BG_BASE, outline=BORDER_CARD, width=1)
        draw.text((80, 412), "LOWEST HF", fill=TEXT_MUTED, font=font_small)
        draw.text((80, 428), "1.12", fill=WARN_RED, font=font_bold)
        
        draw.text((180, 412), "LIQUIDATION AT", fill=TEXT_MUTED, font=font_small)
        draw.text((180, 428), "1.00", fill=WARN_RED, font=font_bold)
        
        draw.text((290, 412), "RESTORED TO", fill=TEXT_MUTED, font=font_small)
        draw.text((290, 428), "1.62", fill=SAFE_TEAL, font=font_bold)

        # 6. Widescreen Vector Chart (Right Panel)
        draw_rounded_card(img, draw, 440, 140, 920, 470, 14, fill=BG_CARD, outline=BORDER_CARD, width=1)
        draw.text((470, 155), "HEALTH FACTOR TIMELINE", fill=TEXT_MUTED, font=font_bold)
        
        # Draw the main mathematical curve line
        curve_points = []
        for cx in range(470, 890, 4):
            cy = get_curve_y(cx)
            curve_points.append((cx, cy))
            
        draw.line(curve_points, fill=SAFE_TEAL, width=3)
        
        # Draw the 1.0x liquidation dotted line
        draw.line([(470, 390), (890, 390)], fill=WARN_RED, width=2)
        draw.text((470, 398), "Liquidation Threshold · 1.0x", fill=WARN_RED, font=font_small)
        
        # Draw the 1.1x Vanna Safety Floor dotted line
        draw.line([(470, 350), (890, 350)], fill=VIOL_PINK, width=2)
        draw.text((720, 328), "Vanna Floor · 1.1x", fill=VIOL_PINK, font=font_small)
        
        # 7. User Position Dot (Glowing Yellow Particle) running along the curve
        # Move the dot dynamically along the X-axis from x=470 to x=890
        t = f / float(total_frames)
        dot_x = int(470 + (890 - 470) * t)
        dot_y = get_curve_y(dot_x)
        
        # If the dot is on the floor (around x = 620 to 680), show the pulsing shield
        is_floor = 620 <= dot_x <= 680
        shield_pulse = 0
        if is_floor:
            shield_pulse = int(12 + 18 * ((f - 20) % 3) / 3.0)
            
        draw_neon_dot(img, draw, dot_x, dot_y, 10, GLOW_YELLOW)
        
        if shield_pulse > 0:
            draw.ellipse([dot_x - shield_pulse, dot_y - shield_pulse, dot_x + shield_pulse, dot_y + shield_pulse], outline=VIOL_PINK, width=3)
            draw.text((dot_x - 65, dot_y - 35), "⚡ Guardian Acted", fill=VIOL_PINK, font=font_bold)
            
        # Draw simple date axis at bottom of the chart
        draw.text((470, 440), "00:00", fill=TEXT_MUTED, font=font_small)
        draw.text((580, 440), "02:00", fill=TEXT_MUTED, font=font_small)
        draw.text((646, 440), "03:14", fill=VIOL_PINK, font=font_small)
        draw.text((750, 440), "04:00", fill=TEXT_MUTED, font=font_small)
        draw.text((860, 440), "06:00", fill=TEXT_MUTED, font=font_small)
        
        frames.append(img)
        
    # Compile the frames into the final high-fidelity widescreen GIF
    frames[0].save(
        str(OUT_GIF),
        save_all=True,
        append_images=frames[1:],
        duration=70, # 70ms per frame = ~14fps (extremely smooth!)
        loop=0
    )
    print(f"✅ Success! Compiled Agentic V12 premium horizontal GIF at: {OUT_GIF}")

if __name__ == "__main__":
    main()
