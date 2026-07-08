import os
import shutil
import wave
import struct
import subprocess
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS
from app.core.config import settings, logger
from app.models.schemas import Storyboard, StoryboardScene
from app.storyboards.content_registry import register_drawer, DRAWING_REGISTRY
from app.core.interfaces import IVideoRendererProvider

# Helper to wrap text for narration captions
def wrap_text(text: str, font, max_width: int) -> list:
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        test_line = " ".join(current_line + [word]) if current_line else word
        bbox = font.getbbox(test_line)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
    return lines

# Drawing Primitive Drawers

@register_drawer("ph_scale_overview")
def draw_ph_scale_overview(draw: ImageDraw.ImageDraw, w: int, h: int, progress: float, font, bold_font):
    # Draw dark slate background
    draw.rectangle([0, 0, w, h], fill="#1a1a2e")
    
    # Title
    draw.text((w // 2, 80), "The pH Scale (0 - 14)", fill="#ffffff", font=bold_font, anchor="mm")
    
    # Draw horizontal gradient pH scale bar
    bar_y = h // 2 - 20
    bar_h = 40
    bar_w = int(w * 0.8)
    bar_x = (w - bar_w) // 2
    
    # Colors: Red (0, acid) -> Green (7, neutral) -> Violet/Blue (14, basic)
    for x_offset in range(bar_w):
        frac = x_offset / bar_w
        # Interpolate color components
        if frac < 0.5:  # Red to Green
            sub_frac = frac * 2.0
            r = int(255 * (1 - sub_frac))
            g = int(255 * sub_frac)
            b = 0
        else:  # Green to Purple
            sub_frac = (frac - 0.5) * 2.0
            r = 0
            g = int(255 * (1 - sub_frac))
            b = int(255 * sub_frac)
        draw.line([bar_x + x_offset, bar_y, bar_x + x_offset, bar_y + bar_h], fill=(r, g, b), width=1)
        
    # Scale lines and numbers
    for i in range(15):
        tick_x = bar_x + int((i / 14.0) * bar_w)
        draw.line([tick_x, bar_y + bar_h, tick_x, bar_y + bar_h + 10], fill="#ffffff", width=2)
        draw.text((tick_x, bar_y + bar_h + 25), str(i), fill="#e0e0e0", font=font, anchor="mm")
        
    # Floating cursor showing progress animation
    cursor_val = progress * 14.0
    cursor_x = bar_x + int(progress * bar_w)
    
    # Draw cursor pin pointing to scale
    draw.polygon([
        (cursor_x, bar_y - 5),
        (cursor_x - 10, bar_y - 20),
        (cursor_x + 10, bar_y - 20)
    ], fill="#ffffff")
    draw.text((cursor_x, bar_y - 35), f"pH: {cursor_val:.1f}", fill="#ffffff", font=bold_font, anchor="mm")

@register_drawer("acidic_solution")
def draw_acidic_solution(draw: ImageDraw.ImageDraw, w: int, h: int, progress: float, font, bold_font):
    draw.rectangle([0, 0, w, h], fill="#1a1a2e")
    
    # Title
    draw.text((w // 2, 80), "Acidic Solution (pH < 7)", fill="#ff4d4d", font=bold_font, anchor="mm")
    
    # Draw beaker outline
    beaker_w = 200
    beaker_h = 240
    beaker_x = w // 2 - beaker_w // 2
    beaker_y = h // 2 - 100
    
    # Liquid height animates slightly
    liq_level = beaker_y + beaker_h - 40 - int(math.sin(progress * 2 * math.pi) * 5)
    
    # Draw liquid area (yellow/orange for acid indicator)
    draw.rectangle([beaker_x + 10, liq_level, beaker_x + beaker_w - 10, beaker_y + beaker_h - 10], fill="#ff7733")
    
    # Draw beaker body
    draw.line([beaker_x, beaker_y, beaker_x, beaker_y + beaker_h], fill="#ffffff", width=4)
    draw.line([beaker_x + beaker_w, beaker_y, beaker_x + beaker_w, beaker_y + beaker_h], fill="#ffffff", width=4)
    draw.line([beaker_x, beaker_y + beaker_h, beaker_x + beaker_w, beaker_y + beaker_h], fill="#ffffff", width=4)
    
    # Draw floating H+ ions bobbing in the acid
    h_positions = [
        (beaker_x + 50, beaker_y + 150),
        (beaker_x + 100, beaker_y + 120),
        (beaker_x + 150, beaker_y + 170),
        (beaker_x + 80, beaker_y + 180)
    ]
    for idx, (hx, hy) in enumerate(h_positions):
        # Bobbing displacement
        dy = int(math.sin(progress * 2 * math.pi + idx) * 15)
        ion_y = hy + dy
        if ion_y > liq_level + 20: # Keep within beaker liquid
            draw.ellipse([hx - 18, ion_y - 18, hx + 18, ion_y + 18], fill="#ff3333", outline="#ffffff", width=2)
            draw.text((hx, ion_y), "H+", fill="#ffffff", font=bold_font, anchor="mm")

@register_drawer("basic_solution")
def draw_basic_solution(draw: ImageDraw.ImageDraw, w: int, h: int, progress: float, font, bold_font):
    draw.rectangle([0, 0, w, h], fill="#1a1a2e")
    
    # Title
    draw.text((w // 2, 80), "Basic Solution (pH > 7)", fill="#3399ff", font=bold_font, anchor="mm")
    
    # Beaker
    beaker_w = 200
    beaker_h = 240
    beaker_x = w // 2 - beaker_w // 2
    beaker_y = h // 2 - 100
    liq_level = beaker_y + beaker_h - 50
    
    # Liquid (blue/purple for basic)
    draw.rectangle([beaker_x + 10, liq_level, beaker_x + beaker_w - 10, beaker_y + beaker_h - 10], fill="#3355cc")
    
    # Draw beaker body
    draw.line([beaker_x, beaker_y, beaker_x, beaker_y + beaker_h], fill="#ffffff", width=4)
    draw.line([beaker_x + beaker_w, beaker_y, beaker_x + beaker_w, beaker_y + beaker_h], fill="#ffffff", width=4)
    draw.line([beaker_x, beaker_y + beaker_h, beaker_x + beaker_w, beaker_y + beaker_h], fill="#ffffff", width=4)
    
    # Draw OH- hydroxide ions
    oh_positions = [
        (beaker_x + 60, beaker_y + 160),
        (beaker_x + 120, beaker_y + 130),
        (beaker_x + 150, beaker_y + 180),
        (beaker_x + 90, beaker_y + 190)
    ]
    for idx, (ox, oy) in enumerate(oh_positions):
        # Wave bobbing
        dy = int(math.cos(progress * 2 * math.pi + idx) * 15)
        ion_y = oy + dy
        if ion_y > liq_level + 20:
            draw.ellipse([ox - 22, ion_y - 18, ox + 22, ion_y + 18], fill="#3399ff", outline="#ffffff", width=2)
            draw.text((ox, ion_y), "OH-", fill="#ffffff", font=bold_font, anchor="mm")

@register_drawer("atoms_intro")
def draw_atoms_intro(draw: ImageDraw.ImageDraw, w: int, h: int, progress: float, font, bold_font):
    draw.rectangle([0, 0, w, h], fill="#1a1a2e")
    draw.text((w // 2, 80), "Unstable Outer Shells", fill="#ffffff", font=bold_font, anchor="mm")
    
    # Draw two atoms separately
    # Left Atom (Chlorine or Oxygen-like)
    ax1, ay1 = w // 4 + 40, h // 2 - 20
    draw.ellipse([ax1 - 60, ay1 - 60, ax1 + 60, ay1 + 60], outline="#ffffff", width=1) # Outer Shell
    draw.ellipse([ax1 - 20, ay1 - 20, ax1 + 20, ay1 + 20], fill="#ff5555") # Nucleus
    draw.text((ax1, ay1), "A", fill="#ffffff", font=font, anchor="mm")
    
    # Dots representing outer electrons (unstable shell)
    electrons_a = [(ax1 - 60, ay1), (ax1 + 60, ay1), (ax1, ay1 - 60)]
    for ex, ey in electrons_a:
        draw.ellipse([ex - 6, ey - 6, ex + 6, ey + 6], fill="#00ff00")
        
    # Right Atom
    ax2, ay2 = 3 * w // 4 - 40, h // 2 - 20
    draw.ellipse([ax2 - 60, ay2 - 60, ax2 + 60, ay2 + 60], outline="#ffffff", width=1)
    draw.ellipse([ax2 - 20, ay2 - 20, ax2 + 20, ay2 + 20], fill="#5555ff")
    draw.text((ax2, ay2), "B", fill="#ffffff", font=font, anchor="mm")
    
    electrons_b = [(ax2 - 60, ay2), (ax2 + 60, ay2), (ax2, ay2 + 60)]
    for ex, ey in electrons_b:
        draw.ellipse([ex - 6, ey - 6, ex + 6, ey + 6], fill="#00ff00")

@register_drawer("electron_sharing")
def draw_electron_sharing(draw: ImageDraw.ImageDraw, w: int, h: int, progress: float, font, bold_font):
    draw.rectangle([0, 0, w, h], fill="#1a1a2e")
    draw.text((w // 2, 80), "Sharing Electron Pairs", fill="#00ff00", font=bold_font, anchor="mm")
    
    # Atoms moving towards each other based on progress
    max_offset = w // 10
    offset = int(progress * max_offset)
    
    ax1, ay1 = w // 4 + 40 + offset, h // 2 - 20
    ax2, ay2 = 3 * w // 4 - 40 - offset, h // 2 - 20
    
    # Draw shell rings
    draw.ellipse([ax1 - 70, ay1 - 70, ax1 + 70, ay1 + 70], outline="#888888", width=1)
    draw.ellipse([ax2 - 70, ay2 - 70, ax2 + 70, ay2 + 70], outline="#888888", width=1)
    
    # Nucleus
    draw.ellipse([ax1 - 22, ay1 - 22, ax1 + 22, ay1 + 22], fill="#ff5555")
    draw.text((ax1, ay1), "A", fill="#ffffff", font=font, anchor="mm")
    
    draw.ellipse([ax2 - 22, ay2 - 22, ax2 + 22, ay2 + 22], fill="#5555ff")
    draw.text((ax2, ay2), "B", fill="#ffffff", font=font, anchor="mm")
    
    # Drawing sharing electrons in overlap zone
    overlap_x = (ax1 + ax2) // 2
    # Electrons orbit the center
    angle = progress * 4 * math.pi
    ex1 = overlap_x + int(math.cos(angle) * 15)
    ey1 = h // 2 - 20 + int(math.sin(angle) * 15)
    
    ex2 = overlap_x - int(math.cos(angle) * 15)
    ey2 = h // 2 - 20 - int(math.sin(angle) * 15)
    
    draw.ellipse([ex1 - 8, ey1 - 8, ex1 + 8, ey1 + 8], fill="#00ff00", outline="#ffffff", width=1)
    draw.ellipse([ex2 - 8, ey2 - 8, ex2 + 8, ey2 + 8], fill="#00ff00", outline="#ffffff", width=1)

@register_drawer("molecule_formation")
def draw_molecule_formation(draw: ImageDraw.ImageDraw, w: int, h: int, progress: float, font, bold_font):
    draw.rectangle([0, 0, w, h], fill="#1a1a2e")
    draw.text((w // 2, 80), "Stable Molecule Formed", fill="#ffffff", font=bold_font, anchor="mm")
    
    # Completely merged covalent bond
    ax1, ay1 = w // 2 - 70, h // 2 - 20
    ax2, ay2 = w // 2 + 70, h // 2 - 20
    
    # Orbit overlap outline
    draw.ellipse([ax1 - 70, ay1 - 70, ax1 + 70, ay1 + 70], outline="#ffffff", width=2)
    draw.ellipse([ax2 - 70, ay2 - 70, ax2 + 70, ay2 + 70], outline="#ffffff", width=2)
    
    # Central bond connecting line
    draw.line([ax1, ay1, ax2, ay2], fill="#00ff00", width=4)
    
    # Nuclei
    draw.ellipse([ax1 - 25, ay1 - 25, ax1 + 25, ay1 + 25], fill="#ff5555")
    draw.text((ax1, ay1), "A", fill="#ffffff", font=font, anchor="mm")
    
    draw.ellipse([ax2 - 25, ay2 - 25, ax2 + 25, ay2 + 25], fill="#5555ff")
    draw.text((ax2, ay2), "B", fill="#ffffff", font=font, anchor="mm")
    
    # Two glowing shared electrons in the middle
    mid_x = w // 2
    ey1 = h // 2 - 35 + int(math.sin(progress * 4 * math.pi) * 5)
    ey2 = h // 2 - 5 - int(math.sin(progress * 4 * math.pi) * 5)
    
    draw.ellipse([mid_x - 8, ey1 - 8, mid_x + 8, ey1 + 8], fill="#00ff00", outline="#ffffff", width=1)
    draw.ellipse([mid_x - 8, ey2 - 8, mid_x + 8, ey2 + 8], fill="#00ff00", outline="#ffffff", width=1)

@register_drawer("bond_comparison")
def draw_bond_comparison(draw: ImageDraw.ImageDraw, w: int, h: int, progress: float, font, bold_font):
    draw.rectangle([0, 0, w, h], fill="#1a1a2e")
    draw.text((w // 2, 80), "Ionic vs Covalent Bonds", fill="#ffffff", font=bold_font, anchor="mm")
    
    # Compare side by side panels
    box_w = w // 2 - 80
    box_h = h // 2
    
    # Left box: Ionic (Transfer)
    bx1 = 50
    by = 130
    draw.rectangle([bx1, by, bx1 + box_w, by + box_h], outline="#ff9933", width=2)
    draw.text((bx1 + box_w // 2, by + 30), "IONIC", fill="#ff9933", font=bold_font, anchor="mm")
    draw.text((bx1 + box_w // 2, by + 100), "Electron Transfer", fill="#e0e0e0", font=font, anchor="mm")
    draw.text((bx1 + box_w // 2, by + 150), "[ Na+ ]  -->  [ Cl- ]", fill="#ff9933", font=bold_font, anchor="mm")
    
    # Right box: Covalent (Sharing)
    bx2 = w // 2 + 30
    draw.rectangle([bx2, by, bx2 + box_w, by + box_h], outline="#33cc33", width=2)
    draw.text((bx2 + box_w // 2, by + 30), "COVALENT", fill="#33cc33", font=bold_font, anchor="mm")
    draw.text((bx2 + box_w // 2, by + 100), "Electron Sharing", fill="#e0e0e0", font=font, anchor="mm")
    draw.text((bx2 + box_w // 2, by + 150), "[ H ]  <==>  [ H ]", fill="#33cc33", font=bold_font, anchor="mm")

@register_drawer("ionic_interaction")
def draw_ionic_interaction(draw: ImageDraw.ImageDraw, w: int, h: int, progress: float, font, bold_font):
    draw.rectangle([0, 0, w, h], fill="#1a1a2e")
    draw.text((w // 2, 80), "Ionic Bond: Transfer of Electrons", fill="#ff9933", font=bold_font, anchor="mm")
    
    ax1, ay1 = w // 4 + 40, h // 2 - 20
    ax2, ay2 = 3 * w // 4 - 40, h // 2 - 20
    
    # Sodium (Na) Shell (losing electron)
    draw.ellipse([ax1 - 50, ay1 - 50, ax1 + 50, ay1 + 50], outline="#ffffff", width=1)
    draw.ellipse([ax1 - 20, ay1 - 20, ax1 + 20, ay1 + 20], fill="#ff9933")
    draw.text((ax1, ay1), "Na+", fill="#ffffff", font=font, anchor="mm")
    
    # Chlorine (Cl) Shell (gaining electron)
    draw.ellipse([ax2 - 55, ay2 - 55, ax2 + 55, ay2 + 55], outline="#ffffff", width=1)
    draw.ellipse([ax2 - 22, ay2 - 22, ax2 + 22, ay2 + 22], fill="#33aa33")
    draw.text((ax2, ay2), "Cl-", fill="#ffffff", font=font, anchor="mm")
    
    # Electron transfer animation
    # Electron dot slides from Na shell to Cl shell
    start_x = ax1 + 50
    end_x = ax2 - 55
    e_x = start_x + int(progress * (end_x - start_x))
    draw.ellipse([e_x - 8, ay1 - 8, e_x + 8, ay1 + 8], fill="#00ff00", outline="#ffffff", width=1)
    
    # Electrostatic attraction arrows (glowing field)
    if progress > 0.8:
        draw.line([ax1 + 60, ay1, ax2 - 65, ay2], fill="#ffff00", width=3)
        draw.text((w // 2, h // 2 - 50), "Attraction!", fill="#ffff00", font=font, anchor="mm")

@register_drawer("covalent_interaction")
def draw_covalent_interaction(draw: ImageDraw.ImageDraw, w: int, h: int, progress: float, font, bold_font):
    draw.rectangle([0, 0, w, h], fill="#1a1a2e")
    # Delegate rendering to the sharing overlap primitive
    draw_electron_sharing(draw, w, h, progress, font, bold_font)
    # Title override
    draw.rectangle([0, 0, w, 110], fill="#1a1a2e")
    draw.text((w // 2, 80), "Covalent Bond: Electron Sharing", fill="#33cc33", font=bold_font, anchor="mm")

@register_drawer("photosynthesis_chloroplast")
def draw_photosynthesis_chloroplast(draw: ImageDraw.ImageDraw, w: int, h: int, progress: float, font, bold_font):
    # Dark forest/leaf green background
    draw.rectangle([0, 0, w, h], fill="#0f2b20")
    
    # Title
    draw.text((w // 2, 80), "Stage 1: Chloroplasts & Chlorophyll", fill="#a3e2c9", font=bold_font, anchor="mm")
    
    # Draw leaf cell outline
    draw.rectangle([60, 130, w - 60, h - 120], outline="#4caf50", width=4)
    draw.text((w // 2, 150), "Plant Leaf Cell", fill="#81c784", font=font, anchor="mm")
    
    # Draw chloroplast organelles (ovals)
    num_chloroplasts = 3
    for i in range(num_chloroplasts):
        cx = w // 2 + (i - 1) * 200
        cy = h // 2
        # Pulsate size with progress
        pulse = int(math.sin(progress * 2 * math.pi) * 8)
        draw.ellipse([cx - 70 - pulse, cy - 40 - pulse, cx + 70 + pulse, cy + 40 + pulse], fill="#2e7d32", outline="#81c784", width=2)
        draw.text((cx, cy), "Chloroplast", fill="#ffffff", font=font, anchor="mm")
        
    # Draw light rays from top-left
    ray_progress = int(progress * 80)
    for i in range(5):
        start_x = 50 + i * 40
        start_y = 0
        end_x = start_x + 100 + ray_progress
        end_y = 200 + ray_progress
        draw.line([start_x, start_y, end_x, end_y], fill="#fdd835", width=3)
    draw.text((100, 40), "Light Energy", fill="#fdd835", font=bold_font)

@register_drawer("light_reaction")
def draw_light_reaction(draw: ImageDraw.ImageDraw, w: int, h: int, progress: float, font, bold_font):
    # Dark forest green background
    draw.rectangle([0, 0, w, h], fill="#0f2b20")
    
    # Title
    draw.text((w // 2, 80), "Stage 2: Splitting Water (H2O)", fill="#64b5f6", font=bold_font, anchor="mm")
    
    # Draw water molecule in center
    mx, my = w // 2, h // 2
    
    # Split distance increases with progress
    split_dist = int(progress * 120)
    
    # Draw Oxygen atom (red)
    ox, oy = mx, my - split_dist // 2
    draw.ellipse([ox - 40, oy - 40, ox + 40, oy + 40], fill="#e53935", outline="#ffffff", width=2)
    draw.text((ox, oy), "O2", fill="#ffffff", font=bold_font, anchor="mm")
    
    # Draw two Hydrogen atoms moving away in opposite directions
    hx1, hy1 = mx - 80 - split_dist, my + 30 + split_dist // 2
    hx2, hy2 = mx + 80 + split_dist, my + 30 + split_dist // 2
    
    draw.ellipse([hx1 - 25, hy1 - 25, hx1 + 25, hy1 + 25], fill="#1e88e5", outline="#ffffff", width=2)
    draw.text((hx1, hy1), "H+", fill="#ffffff", font=font, anchor="mm")
    
    draw.ellipse([hx2 - 25, hy2 - 25, hx2 + 25, hy2 + 25], fill="#1e88e5", outline="#ffffff", width=2)
    draw.text((hx2, hy2), "H+", fill="#ffffff", font=font, anchor="mm")
    
    # Draw dashed connecting lines that fade out (only draw if progress is low)
    if progress < 0.7:
        draw.line([ox, oy, hx1, hy1], fill="#e0e0e0", width=2)
        draw.line([ox, oy, hx2, hy2], fill="#e0e0e0", width=2)
        
    draw.text((w // 2, h // 2 + 150), "Oxygen gas is released!", fill="#ffffff", font=bold_font, anchor="mm")

@register_drawer("glucose_production")
def draw_glucose_production(draw: ImageDraw.ImageDraw, w: int, h: int, progress: float, font, bold_font):
    # Dark forest green background
    draw.rectangle([0, 0, w, h], fill="#0f2b20")
    
    # Title
    draw.text((w // 2, 80), "Stage 3: Glucose Synthesis", fill="#a5d6a7", font=bold_font, anchor="mm")
    
    # Chloroplast reactor in center
    rx, ry = w // 2, h // 2 + 20
    draw.ellipse([rx - 150, ry - 80, rx + 150, ry + 80], fill="#1b5e20", outline="#81c784", width=3)
    draw.text((rx, ry), "Calvin Cycle", fill="#ffffff", font=bold_font, anchor="mm")
    
    # Carbon Dioxide (CO2) entering from left
    co2_x = 50 + int(progress * (rx - 150 - 50))
    if co2_x < rx - 140:
        draw.ellipse([co2_x - 30, ry - 30, co2_x + 30, ry + 30], fill="#ffb74d", outline="#ffffff", width=1)
        draw.text((co2_x, ry), "CO2", fill="#ffffff", font=font, anchor="mm")
        
    # Glucose (Sugar) exiting from right
    if progress > 0.4:
        sugar_progress = (progress - 0.4) / 0.6
        sugar_x = rx + 150 + int(sugar_progress * (w - 150 - (rx + 150)))
        draw.ellipse([sugar_x - 35, ry - 35, sugar_x + 35, ry + 35], fill="#81c784", outline="#ffffff", width=2)
        draw.text((sugar_x, ry), "Glucose", fill="#ffffff", font=font, anchor="mm")
        draw.text((sugar_x, ry + 50), "C6H12O6", fill="#a5d6a7", font=font, anchor="mm")

# Global Fallback Drawer
def draw_default_scene(draw: ImageDraw.ImageDraw, w: int, h: int, progress: float, font, bold_font):
    draw.rectangle([0, 0, w, h], fill="#1a1a2e")
    draw.text((w // 2, h // 2 - 20), "Educational Chemistry Lesson", fill="#ffffff", font=bold_font, anchor="mm")
    draw.text((w // 2, h // 2 + 30), f"Animation progress: {progress * 100.0:.0f}%", fill="#a0a0a0", font=font, anchor="mm")


def generate_silent_audio(output_path: str, duration: float) -> None:
    """
    Generates a silent mono WAV file at 22050Hz, 16-bit, for the estimated duration.
    """
    sample_rate = 22050
    num_samples = int(duration * sample_rate)
    with wave.open(output_path, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        # Write silence frames (zeros)
        silence_bytes = struct.pack('<h', 0) * num_samples
        wav.writeframesraw(silence_bytes)


# Global Process Drawing Target (Must be top-level for ProcessPoolExecutor serialization)
def execute_frame_render_process(
    frame_idx: int,
    total_frames: int,
    visual_type: str,
    script_text: str,
    font_path: str,
    width: int,
    height: int,
    output_path: str
) -> None:
    # Set progress fraction
    progress = frame_idx / max(1, total_frames - 1)
    
    # Instantiate new blank frame
    img = Image.new("RGBA", (width, height), "#1a1a2e")
    draw = ImageDraw.Draw(img)
    
    # Font setup
    try:
        font = ImageFont.truetype(font_path, 22)
        bold_font = ImageFont.truetype(font_path, 26)
        
        # Dynamically scale font size based on text length to prevent line overflows
        cap_size = 20
        if len(script_text) > 130:
            cap_size = 15
        elif len(script_text) > 90:
            cap_size = 17
            
        caption_font = ImageFont.truetype(font_path, cap_size)
    except Exception:
        font = ImageFont.load_default()
        bold_font = ImageFont.load_default()
        caption_font = ImageFont.load_default()
        cap_size = 20

    # Call drawing logic matching visual_type
    drawer_func = DRAWING_REGISTRY.get(visual_type, draw_default_scene)
    drawer_func(draw, width, height, progress, font, bold_font)
    
    # Draw transparent caption bar at bottom
    caption_h = 90
    draw.rectangle([0, height - caption_h, width, height], fill="#000000d0")
    
    # Wrap text and render lines
    max_caption_w = int(width * 0.9)
    wrapped_lines = wrap_text(script_text, caption_font, max_caption_w)
    
    # Calculate spacing and center text in caption bar
    start_y = height - caption_h + 15
    line_spacing = cap_size + 4
    for i, line in enumerate(wrapped_lines[:4]): # Allow up to 4 lines with smaller font size
        draw.text((width // 2, start_y + (i * line_spacing)), line, fill="#ffffff", font=caption_font, anchor="mm")
        
    # Save output frame PNG
    img.save(output_path, "PNG")


class VideoRendererProvider(IVideoRendererProvider):
    def __init__(self) -> None:
        self.width = settings.video_resolution_w
        self.height = settings.video_resolution_h
        self.fps = settings.video_fps
        logger.info(f"VideoRenderer initialized. Format: {self.width}x{self.height} @ {self.fps}fps")

    def synthesize_speech(self, text: str, output_path: str, locale: str = "en-US") -> str:
        """
        Generate audio speech file for the scene. Falls back to native macOS say utility or silent tone WAV on failure.
        """
        logger.info(f"Renderer: Synthesizing voiceover for text: '{text[:50]}...'")
        try:
            # Run gTTS voice generation
            tts = gTTS(text=text, lang="en")
            tts.save(output_path)
            logger.info(f"gTTS speech saved to: {output_path}")
            return output_path
        except Exception as e:
            logger.warning(f"gTTS Speech synthesis failed: {str(e)}. Attempting local native speech synthesis...")
            # Try macOS native say utility
            try:
                aiff_temp = output_path.replace(".mp3", ".aiff").replace(".wav", ".aiff")
                cmd = ["/usr/bin/say", "-v", "Samantha", "-o", aiff_temp, text]
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if result.returncode == 0 and os.path.exists(aiff_temp):
                    # Convert AIFF to target audio format using FFmpeg
                    convert_cmd = ["ffmpeg", "-y", "-i", aiff_temp, "-threads", "2", output_path]
                    subprocess.run(convert_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                    os.remove(aiff_temp)
                    logger.info(f"Native macOS say synthesized and transcoded speech to: {output_path}")
                    return output_path
            except Exception as say_err:
                logger.warning(f"Native macOS say synthesis failed: {str(say_err)}. Generating silent WAV file.")

            # Calculate word count to estimate speaking duration (~150 words per minute)
            word_count = len(text.split())
            estimated_duration = max(3.0, (word_count / 150.0) * 60.0)
            
            # Generate local silent WAV file
            generate_silent_audio(output_path, estimated_duration)
            logger.info(f"Silent wave fallback generated successfully. Path: {output_path}, Duration: {estimated_duration}s")
            return output_path

    def draw_scene_frames(self, scene: StoryboardScene, audio_path: str, temp_dir: str) -> str:
        """
        Calculates animation frames, draws images via ProcessPoolExecutor, and compiles scene MP4.
        """
        # Defer import to prevent circular import issues
        from app.workers.scheduler import scheduler
        
        # Get actual audio duration using ffprobe
        duration = self.get_audio_duration(audio_path)
        if not duration:
            logger.warning(f"Could not determine audio length. Defaulting to storyboard duration: {scene.duration}s")
            duration = scene.duration
            
        # Add 12 frames (0.5 second) of holding padding to ensure video is always longer than audio,
        # preventing FFmpeg's -shortest flag from truncating the final words of the voiceover.
        total_frames = math.ceil(duration * self.fps) + 12
        logger.info(f"Scene processing: duration {duration:.2f}s, frame count {total_frames} frames (includes 12 frames padding).")
        
        # Create temp folder for frames
        frames_dir = Path(temp_dir) / "frames"
        os.makedirs(frames_dir, exist_ok=True)
        
        # Dispatch rendering tasks to ProcessPoolExecutor for GIL bypass isolation
        executor = scheduler.get_executor()
        futures = []
        
        for frame_idx in range(total_frames):
            frame_file = frames_dir / f"frame_{frame_idx:04d}.png"
            # Submit task to pool
            f = executor.submit(
                execute_frame_render_process,
                frame_idx,
                total_frames,
                scene.visual_type,
                scene.script,
                str(settings.font_path),
                self.width,
                self.height,
                str(frame_file)
            )
            futures.append(f)
            
        # Wait for all processes to complete
        for f in futures:
            f.result()
            
        logger.info(f"Pillow drawing completed. 100% of frames rendered inside: {frames_dir}")
        
        # Compile frames & audio into temporary scene video file
        scene_output = Path(temp_dir) / "scene_output.mp4"
        
        # Stitch PNG frames & WAV/MP3 track using FFmpeg CLI
        cmd = [
            "ffmpeg", "-y",
            "-r", str(self.fps),
            "-f", "image2",
            "-i", str(frames_dir / "frame_%04d.png"),
            "-i", str(audio_path),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-shortest",
            "-threads", "2",  # Restrict threads to prevent starving server core availability
            str(scene_output)
        ]
        
        logger.info(f"Running FFmpeg scene compiler: {' '.join(cmd)}")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if result.returncode != 0:
            err_msg = result.stderr.decode("utf-8")
            logger.error(f"FFmpeg scene compilation failed: {err_msg}")
            raise RuntimeError(f"FFmpeg scene compilation failed: {err_msg}")
            
        logger.info(f"FFmpeg compiled scene MP4 successfully. Saved: {scene_output}")
        return str(scene_output)

    def get_audio_duration(self, audio_path: str) -> float:
        """
        Runs ffprobe subprocess to inspect exact audio length. Returns 0.0 on failure.
        """
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_path)
        ]
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            duration_str = result.stdout.decode("utf-8").strip()
            return float(duration_str)
        except Exception as e:
            logger.warning(f"FFprobe check failed for {audio_path}: {str(e)}")
            return 0.0

    def render_job_video(self, job_id: str, storyboard: Storyboard) -> str:
        """
        Executes end-to-end rendering pipeline, stitching all scenes, running checks and cleanup.
        """
        job_temp = settings.temp_dir / job_id
        os.makedirs(job_temp, exist_ok=True)
        
        scene_files = []
        
        try:
            # Process each scene
            for idx, scene in enumerate(storyboard.scenes):
                logger.info(f"Rendering scene {idx + 1}/{len(storyboard.scenes)} (Visual: {scene.visual_type})")
                scene_temp = job_temp / f"scene_{idx}"
                os.makedirs(scene_temp, exist_ok=True)
                
                # Speech audio track synthesis
                audio_ext = "mp3"
                audio_file = scene_temp / f"speech.{audio_ext}"
                self.synthesize_speech(scene.script, str(audio_file))
                
                # Render animation frames and stitch into scene MP4
                scene_mp4 = self.draw_scene_frames(scene, str(audio_file), str(scene_temp))
                scene_files.append(scene_mp4)
                
            # Concatenate all scene clips into a single final video
            final_output = settings.static_dir / f"{job_id}.mp4"
            concat_file = job_temp / "concat.txt"
            
            with open(concat_file, "w") as f:
                for sf in scene_files:
                    # Write file paths for FFmpeg concat filter
                    f.write(f"file '{sf}'\n")
                    
            logger.info(f"Stitching {len(scene_files)} scene clips using FFmpeg concat list...")
            concat_cmd = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file),
                "-c", "copy",
                "-threads", "2",
                str(final_output)
            ]
            
            result = subprocess.run(concat_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode != 0:
                err_msg = result.stderr.decode("utf-8")
                raise RuntimeError(f"FFmpeg video concatenation failed: {err_msg}")
                
            # Perform Quality Assurance automated audit via FFprobe
            self.verify_media_integrity(str(final_output))
            
            logger.info(f"Video compilation succeeded. Artifact saved in: {final_output}")
            return f"/static/{job_id}.mp4"
            
        finally:
            # Purge all temp files and frames immediately to prevent disk leakages
            if os.path.exists(job_temp):
                logger.info(f"Purging temporary directory: {job_temp}")
                shutil.rmtree(job_temp, ignore_errors=True)

    def verify_media_integrity(self, filepath: str) -> None:
        """
        Runs automated audits on the generated video via FFprobe.
        Throws exception if specs do not match expected criteria.
        """
        logger.info(f"QA: Auditing output media structure: {filepath}")
        
        # Check if file exists and has size
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            raise ValueError("Output video file is missing or empty.")
            
        # Inspect duration, resolution, framerate via ffprobe
        cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height,avg_frame_rate,duration",
            "-of", "csv=p=0",
            filepath
        ]
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            stdout = result.stdout.decode("utf-8").strip()
            # Expected format: width,height,fps,duration (e.g. "1280,720,24/1,20.5")
            parts = stdout.split(",")
            if len(parts) < 4:
                raise ValueError(f"FFprobe audit returned insufficient attributes: {stdout}")
                
            w = int(parts[0])
            h = int(parts[1])
            fps_frac = parts[2]
            duration = float(parts[3])
            
            # Compute FPS float
            if "/" in fps_frac:
                num, denom = map(float, fps_frac.split("/"))
                fps = num / denom
            else:
                fps = float(fps_frac)
                
            logger.info(f"QA Specs Checked: Resolution {w}x{h}, FPS {fps:.1f}, Duration {duration:.2f}s")
            
            if w != settings.video_resolution_w or h != settings.video_resolution_h:
                raise ValueError(f"QA Failed: video resolution is {w}x{h}, expected {settings.video_resolution_w}x{settings.video_resolution_h}")
                
            if abs(fps - settings.video_fps) > 0.5:
                raise ValueError(f"QA Failed: video framerate is {fps:.1f}, expected {settings.video_fps} FPS")
                
            if duration <= 0.0 or duration > 30.0:
                raise ValueError(f"QA Failed: video duration is {duration:.2f}s, which violates prototype limit (0s - 30s)")
                
            logger.info("QA verification succeeded: Output artifact matches all NFR standards.")
        except Exception as e:
            logger.error(f"QA Verification exception triggered: {str(e)}")
            raise RuntimeError(f"Video Quality Verification failed: {str(e)}")

# Singleton video renderer instance
video_renderer = VideoRendererProvider()
