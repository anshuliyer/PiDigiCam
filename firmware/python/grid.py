import time
import sys
import select
import numpy as np
import mmap
from picamera2 import Picamera2
from PIL import Image, ImageDraw

# Config
FB_DEVICE = "/dev/fb1" 
SCREEN_RES = (480, 320)
FPS_CAP = 3  # Keeps SPI bus stable

picam2 = Picamera2()

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

def take_photo(fb_map):
    print("\n[SHUTTER] Capturing...")
    picam2.stop()
    config = picam2.create_still_configuration()
    picam2.configure(config)
    picam2.start()
    
    time.sleep(1)
    filename = f"capture_{int(time.time())}.jpg"
    picam2.capture_file(filename)
    
    # Review
    img = Image.open(filename).convert("RGB").resize(SCREEN_RES)
    display_to_map(np.array(img), fb_map)
    time.sleep(2.0)
    
    picam2.stop()
    start_preview()

# --- Grid Logic ---
def apply_grid(data_array):
    """Draws black Rule of Thirds lines on the provided frame."""
    img = Image.fromarray(data_array)
    draw = ImageDraw.Draw(img)
    w, h = SCREEN_RES
    color = (0, 0, 0) # Black
    
    # Vertical lines
    draw.line([(w//3, 0), (w//3, h)], fill=color, width=1)
    draw.line([(2*w//3, 0), (2*w//3, h)], fill=color, width=1)
    # Horizontal lines
    draw.line([(0, h//3), (w, h//3)], fill=color, width=1)
    draw.line([(0, 2*h//3), (w, 2*h//3)], fill=color, width=1)
    
    return np.array(img)

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
                    # Apply grid to the preview frame
                    grid_frame = apply_grid(frame)
                    display_to_map(grid_frame, fb_map)
                
                if select.select([sys.stdin], [], [], 0)[0]:
                    sys.stdin.readline()
                    take_photo(fb_map)
                
                time.sleep(max(0, (1.0 / FPS_CAP) - (time.time() - loop_start)))
except KeyboardInterrupt:
    picam2.stop()
