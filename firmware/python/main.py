import time
import sys
import select
import os
import numpy as np
import mmap
from picamera2 import Picamera2
from PIL import Image, ImageDraw

# Config
FB_DEVICE = "/dev/fb1" 
SCREEN_RES = (480, 320)
FPS_CAP = 3  # Keeps SPI bus stable
MAUVE = (224, 176, 255)

picam2 = Picamera2()
 
def overlay_ui(frame, config):
    """
    Overlays UI indicators on the camera frame with rotation and padding support.
    """
    if config is None:
        return frame
        
    img = Image.fromarray(frame)
    draw = ImageDraw.Draw(img)
    
    rotation = config.get("ui_rotation", 0)
    padding = config.get("ui_padding", 20)
    
    # Calculate base positions based on rotation
    # Assuming the user wants icons in the "top-right" of the current orientation
    w, h = SCREEN_RES
    
    if rotation == 0:
        x_base, y_base = w - padding, padding
    elif rotation == 90:
        x_base, y_base = w - padding, h - padding
    elif rotation == 180:
        x_base, y_base = padding, h - padding
    else: # 270
        x_base, y_base = padding, padding

    # Vertical alignment center
    y_row = y_base + 5
    
    # Flash Icon (Thunderbolt) - Moved up slightly
    if config.get("flash"):
        x, y = x_base - 20, y_row - 12
        points = [
            (x, y), (x - 8, y + 8),
            (x - 4, y + 8), (x - 12, y + 20),
            (x - 4, y + 12), (x - 8, y + 12),
            (x, y)
        ]
        draw.polygon(points, fill=MAUVE)
    
    # Battery Placeholder - Centered on y_row
    x_batt = x_base - 80
    y_batt = y_row - 5
    draw.rectangle([x_batt, y_batt, x_batt + 20, y_batt + 10], outline=MAUVE, width=2)
    draw.rectangle([x_batt + 20, y_batt + 3, x_batt + 22, y_batt + 7], fill=MAUVE)
    
    # WiFi Placeholder - Centered on y_row
    x_wifi = x_base - 140
    y_wifi = y_row - 10
    for i in range(1, 4):
        # Draw small arcs for wifi
        r = i * 4
        bbox = [x_wifi + 10 - r, y_wifi + 10 - r, x_wifi + 10 + r, y_wifi + 10 + r]
        draw.arc(bbox, 225, 315, fill=MAUVE, width=2)

    return np.array(img)


def start_preview():
    config = picam2.create_video_configuration(main={"size": SCREEN_RES, "format": "RGB888"})
    picam2.configure(config)
    picam2.start()

def display_to_map(data_array, fb_map):
    # Convert RGB888 to RGB565 (Little Endian for tft35a)
    r = data_array[:, :, 0].astype(np.uint16)
    g = data_array[:, :, 1].astype(np.uint16)
    b = data_array[:, :, 2].astype(np.uint16)
    
    # Swap R and B if colors look blue/red inverted
    rgb565 = ((b >> 3) << 11) | ((g >> 2) << 5) | (r >> 3)
    
    fb_map.seek(0)
    fb_map.write(rgb565.tobytes())

def take_photo(fb_map, config=None):
    photo_dir = config.get("photo_dir", ".") if config else "."
    if not os.path.exists(photo_dir):
        os.makedirs(photo_dir, exist_ok=True)
        
    print(f"\n[SHUTTER] Capturing to {photo_dir}...")
    picam2.stop()
    config_still = picam2.create_still_configuration()
    picam2.configure(config_still)
    picam2.start()
    
    time.sleep(1)
    filename = os.path.join(photo_dir, f"capture_{int(time.time())}.jpg")
    picam2.capture_file(filename)
    
    # Review
    img = Image.open(filename).convert("RGB").resize(SCREEN_RES)
    display_to_map(np.array(img), fb_map)
    time.sleep(2.0)
    
    picam2.stop()
    start_preview()

def run(config=None):
    # Main Loop
    start_preview()
    try:
        with open(FB_DEVICE, "r+b") as f:
            map_size = SCREEN_RES[0] * SCREEN_RES[1] * 2
            with mmap.mmap(f.fileno(), map_size) as fb_map:
                while True:
                    loop_start = time.time()
                    frame = picam2.capture_array()
                    if frame is not None:
                        frame = overlay_ui(frame, config)
                        display_to_map(frame, fb_map)
                    
                    if select.select([sys.stdin], [], [], 0)[0]:
                        sys.stdin.readline()
                        take_photo(fb_map, config)
                    
                    time.sleep(max(0, (1.0 / FPS_CAP) - (time.time() - loop_start)))
    except KeyboardInterrupt:
        picam2.stop()

if __name__ == "__main__":
    run()
