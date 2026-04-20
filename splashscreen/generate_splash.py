from PIL import Image, ImageDraw
import math
import random

# Configuration
BG_COLOR = (0, 0, 0)
LIGHT_MAUVE = (235, 210, 255)
DARK_MAUVE = (90, 45, 110)
DOTTED_COLOR = (120, 120, 130)

def draw_dotted_line(draw, x1, y1, x2, y2, color, dash, gap, width, chalk=False):
    dx, dy = x2 - x1, y2 - y1
    dist = math.sqrt(dx**2 + dy**2)
    if dist == 0: return
    ux, uy = dx / dist, dy / dist
    curr = 0
    while curr < dist:
        end_dist = min(curr + dash, dist)
        if chalk:
            draw_chalky_line(draw, x1 + ux*curr, y1 + uy*curr, x1 + ux*end_dist, y1 + uy*end_dist, color, width)
        else:
            draw.line([(x1 + ux * curr, y1 + uy * curr), (x1 + ux * end_dist, y1 + uy * end_dist)], fill=color, width=width)
        curr += dash + gap

def draw_chalky_line(draw, x1, y1, x2, y2, color, width):
    draw.line([x1, y1, x2, y2], fill=color, width=width)
    length = math.sqrt((x2-x1)**2 + (y2-y1)**2)
    steps = int(length * 2)
    for s in range(steps):
        t = s / steps
        px = x1 + (x2-x1)*t
        py = y1 + (y2-y1)*t
        for _ in range(3):
            off_x = random.uniform(-width, width)
            off_y = random.uniform(-width, width)
            opacity_var = random.randint(-50, 50)
            p_color = tuple(max(0, min(255, c + opacity_var)) for c in color)
            draw.point((px + off_x, py + off_y), fill=p_color)

def draw_dotted_rect(draw, x, y, size_w, size_h, color, dash, gap, width, chalk=False):
    draw_dotted_line(draw, x, y, x + size_w, y, color, dash, gap, width, chalk)
    draw_dotted_line(draw, x + size_w, y, x + size_w, y + size_h, color, dash, gap, width, chalk)
    draw_dotted_line(draw, x + size_w, y + size_h, x, y + size_h, color, dash, gap, width, chalk)
    draw_dotted_line(draw, x, y + size_h, x, y, color, dash, gap, width, chalk)

def interpolate_color(c1, c2, factor):
    return tuple(int(c1[j] + (c2[j] - c1[j]) * factor) for j in range(3))

def draw_smooth_arc(draw, center_x, center_y, radius, start_deg, end_deg, color, width, chalk=False):
    steps = 400 if chalk else 150
    points = []
    for i in range(steps + 1):
        angle = math.radians(start_deg + (end_deg - start_deg) * i / steps)
        px = center_x + radius * math.cos(angle)
        py = center_y + radius * math.sin(angle)
        if chalk:
            px += random.uniform(-0.5, 0.5)
            py += random.uniform(-0.5, 0.5)
        points.append((px, py))
    if len(points) > 1:
        if chalk:
            for i in range(len(points) - 1):
                p1, p2 = points[i], points[i+1]
                draw_chalky_line(draw, p1[0], p1[1], p2[0], p2[1], color, width)
        else:
            draw.line(points, fill=color, width=width, joint="curve")

def generate_euclid_design(width, height, filename, is_logo=False):
    img = Image.new('RGB', (width, height), BG_COLOR)
    draw = ImageDraw.Draw(img)
    scale = min(width / 320, height / 240)
    max_w, max_h = 300 * scale, 220 * scale
    container_x, container_y = (width - max_w) // 2, (height - max_h) // 2
    main_dash, main_gap, pen_width = int(3 * scale), int(7 * scale), max(1, int(scale))
    
    # if not is_logo:
    #     draw_dotted_rect(draw, container_x, container_y, max_w, max_h, DOTTED_COLOR, main_dash, main_gap, pen_width)

    phi = (1 + 5**0.5) / 2
    curr_x, curr_y = container_x, container_y + (max_h - (max_w / phi)) / 2
    curr_w, curr_h = max_w, max_w / phi
    
    for i in range(12):
        s = min(curr_w, curr_h)
        mode, factor = i % 4, i / 11.0
        color = interpolate_color(DARK_MAUVE, LIGHT_MAUVE, factor)
        arc_width = int(max(int(scale), int((4 - i//3) * scale)) * (1.5 if is_logo else 1))
        draw_dotted_rect(draw, curr_x, curr_y, s, s, DOTTED_COLOR, main_dash, main_gap, pen_width, chalk=is_logo)
        if mode == 0: 
            draw_smooth_arc(draw, curr_x + s, curr_y + s, s, 180, 270, color, arc_width, chalk=is_logo)
            curr_x += s; curr_w -= s
        elif mode == 1:
            draw_smooth_arc(draw, curr_x, curr_y + s, s, 270, 360, color, arc_width, chalk=is_logo)
            curr_y += s; curr_h -= s
        elif mode == 2:
            draw_smooth_arc(draw, curr_x + curr_w - s, curr_y, s, 0, 90, color, arc_width, chalk=is_logo)
            curr_w -= s
        elif mode == 3:
            draw_smooth_arc(draw, curr_x + s, curr_y + curr_h - s, s, 90, 180, color, arc_width, chalk=is_logo)
            curr_h -= s
    
    # Draw EuclidCam title in bottom-left (aligned with GIF)
    text_x, text_y = 20 * scale, height - 50 * scale
    draw_chalky_text(draw, text_x, text_y, "EuclidCam", LIGHT_MAUVE, 14, scale)
    
    img.save(filename, "JPEG", quality=95) if filename.endswith(".jpeg") else img.save(filename)

def generate_svg_design(width, height, filename):
    """
    Generates a high-quality SVG version for 3D printing.
    """
    phi = (1 + 5**0.5) / 2
    max_w, max_h = width * 0.9, height * 0.9
    container_x, container_y = (width - max_w) / 2, (height - max_h) / 2
    curr_x, curr_y = container_x, container_y + (max_h - (max_w / phi)) / 2
    curr_w, curr_h = max_w, max_w / phi
    
    svg_paths = []
    scale = min(width / 320, height / 240)
    
    # Add EuclidCam title in bottom-left (aligned with GIF)
    text_x, text_y = 20 * scale, height - 50 * scale
    svg_paths.append(f'<text x="{text_x}" y="{text_y}" font-family="Chalkboard, cursive" font-size="{int(18*scale)}" fill="black">EuclidCam</text>')
    
    # Loop for geometry
    for i in range(12):
        s = min(curr_w, curr_h)
        mode = i % 4
        
        # Add Square as a simple path (useful for 3D extrusion)
        svg_paths.append(f'<rect x="{curr_x}" y="{curr_y}" width="{s}" height="{s}" fill="none" stroke="black" stroke-width="1" stroke-dasharray="2,2" />')
        
        # Arc mapping to SVG "A" command
        # Large-arc-flag and sweep-flag logic for quarter circles
        if mode == 0: # BL to TR
            x_start, y_start = curr_x, curr_y + s
            x_end, y_end = curr_x + s, curr_y
            svg_paths.append(f'<path d="M {x_start} {y_start} A {s} {s} 0 0 1 {x_end} {y_end}" fill="none" stroke="black" stroke-width="3" />')
            curr_x += s; curr_w -= s
        elif mode == 1: # TL to BR
            x_start, y_start = curr_x, curr_y
            x_end, y_end = curr_x + s, curr_y + s
            svg_paths.append(f'<path d="M {x_start} {y_start} A {s} {s} 0 0 1 {x_end} {y_end}" fill="none" stroke="black" stroke-width="3" />')
            curr_y += s; curr_h -= s
        elif mode == 2: # TR to BL
            x_start, y_start = curr_x + curr_w, curr_y
            x_end, y_end = curr_x + curr_w - s, curr_y + s
            svg_paths.append(f'<path d="M {x_start} {y_start} A {s} {s} 0 0 1 {x_end} {y_end}" fill="none" stroke="black" stroke-width="3" />')
            curr_w -= s
        elif mode == 3: # BR to TL
            x_start, y_start = curr_x + s, curr_y + curr_h
            x_end, y_end = curr_x, curr_y + curr_h - s
            svg_paths.append(f'<path d="M {x_start} {y_start} A {s} {s} 0 0 1 {x_end} {y_end}" fill="none" stroke="black" stroke-width="3" />')
            curr_h -= s

    svg_content = f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">\n'
    svg_content += "\n".join(svg_paths)
    svg_content += "\n</svg>"
    
    with open(filename, "w") as f:
        f.write(svg_content)
    print(f"Generated: {filename} (Vector/Transparent)")

def draw_chalky_text(draw, x, y, text, color, size, scale):
    try:
        from PIL import ImageFont
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Chalkboard.ttc", int(size * scale))
    except Exception:
        font = ImageFont.load_default()
    
    # Draw text multiple times with jitter to simulate "bad" handwriting
    # But remove the background "noise" loop
    for _ in range(3):
        off_x = random.uniform(-1, 1)
        off_y = random.uniform(-1, 1)
        draw.text((x + off_x, y + off_y), text, fill=color, font=font)

def generate_construction_gif(width, height, filename, duration=350):
    frames = []
    img = Image.new('RGB', (width, height), BG_COLOR)
    draw = ImageDraw.Draw(img)
    scale = min(width / 320, height / 240)
    max_w, max_h = 300 * scale, 220 * scale
    container_x, container_y = (width - max_w) // 2, (height - max_h) // 2
    main_dash, main_gap, pen_width = int(3 * scale), int(7 * scale), max(1, int(scale))
    
    # Initial empty frame
    frames.append(img.copy())

    phi = (1 + 5**0.5) / 2
    curr_x, curr_y = container_x, container_y + (max_h - (max_w / phi)) / 2
    curr_w, curr_h = max_w, max_w / phi
    
    radii = []
    
    # Text position: bottom-left, elevated
    text_x, text_y = 20 * scale, height - 50 * scale
    
    for i in range(12):
        s = min(curr_w, curr_h)
        radii.append(int(s/scale)) # Normalize s for display
        
        mode, factor = i % 4, i / 11.0
        color = interpolate_color(DARK_MAUVE, LIGHT_MAUVE, factor)
        arc_width = int(max(int(scale), int((4 - i//3) * scale)))
        
        # Calculate equation text
        if i == 0:
            equation = f"R0 = {radii[0]}"
        elif i == 1:
            equation = f"R1 = {radii[1]}"
        else:
            equation = f"R{i} = R{i-1} + R{i-2} = {radii[i]}"
            
        # Step 1: Draw the square
        draw_dotted_rect(draw, curr_x, curr_y, s, s, DOTTED_COLOR, main_dash, main_gap, pen_width)
        
        # Save frame with equation
        temp_img = img.copy()
        temp_draw = ImageDraw.Draw(temp_img)
        draw_chalky_text(temp_draw, text_x, text_y, equation, LIGHT_MAUVE, 14, scale)
        frames.append(temp_img)
        
        # Step 2: Draw the arc
        if mode == 0: 
            draw_smooth_arc(draw, curr_x + s, curr_y + s, s, 180, 270, color, arc_width)
            curr_x += s; curr_w -= s
        elif mode == 1:
            draw_smooth_arc(draw, curr_x, curr_y + s, s, 270, 360, color, arc_width)
            curr_y += s; curr_h -= s
        elif mode == 2:
            draw_smooth_arc(draw, curr_x + curr_w - s, curr_y, s, 0, 90, color, arc_width)
            curr_w -= s
        elif mode == 3:
            draw_smooth_arc(draw, curr_x + s, curr_y + curr_h - s, s, 90, 180, color, arc_width)
            curr_h -= s
            
        # Save frame with equation
        temp_img = img.copy()
        temp_draw = ImageDraw.Draw(temp_img)
        draw_chalky_text(temp_draw, text_x, text_y, equation, color, 14, scale)
        frames.append(temp_img)
    
    # Hold the final frame for a bit longer and show the title
    for _ in range(15):
        temp_img = img.copy()
        temp_draw = ImageDraw.Draw(temp_img)
        draw_chalky_text(temp_draw, text_x, text_y, "EuclidCam", LIGHT_MAUVE, 18, scale)
        frames.append(temp_img)
        
    frames[0].save(filename, save_all=True, append_images=frames[1:], duration=duration, loop=0)
    print(f"Generated: {filename} (Animated GIF Polished)")

def save_chalk_settings(filename="chalk_settings.json"):
    import json
    settings = {
        "font": "Chalkboard.ttc",
        "colors": {
            "bg": BG_COLOR,
            "light": LIGHT_MAUVE,
            "dark": DARK_MAUVE,
            "dotted": DOTTED_COLOR
        },
        "chalk_effect": {
            "multi_stroke": 3,
            "jitter_range": [-1, 1]
        },
        "layout": {
            "equation_pos": "bottom-left",
            "elevation_px": 50
        }
    }
    with open(filename, "w") as f:
        json.dump(settings, f, indent=4)
    print(f"Saved: {filename}")

if __name__ == "__main__":
    generate_euclid_design(320, 240, "euclid_splash.png")
    generate_euclid_design(1024, 1024, "euclid_logo.jpeg", is_logo=True)
    generate_svg_design(1000, 1000, "transparent.svg")
    generate_construction_gif(640, 480, "euclid_construction.gif")
    save_chalk_settings()