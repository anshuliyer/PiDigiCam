import time
import sys
import select
import os
import numpy as np
import mmap
from picamera2 import Picamera2
from PIL import Image, ImageDraw
from UI import ui_top
from IO import keyboard_gpio_stubs as io_stubs

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
    if config is None:
        config = {}
        
    # Initialize menu index
    if "menu_index" not in config:
        config["menu_index"] = 0
        
    panel = ui_top.TopPanel(config, SCREEN_RES)
    kbd = io_stubs.KeyboardInterface()
    start_preview()
    try:
        with open(FB_DEVICE, "r+b") as f:
            map_size = SCREEN_RES[0] * SCREEN_RES[1] * 2
            with mmap.mmap(f.fileno(), map_size) as fb_map:
                while True:
                    loop_start = time.time()
                    frame = picam2.capture_array()
                    if frame is not None:
                        frame = panel.render(frame)
                        display_to_map(frame, fb_map)
                    
                    key = kbd.get_input()
                    if key == "ENTER":
                        take_photo(fb_map, config)
                    elif key == "SPACE":
                        config["show_menu"] = not config.get("show_menu", False)
                        print(f"[SYSTEM] Settings menu: {'OPEN' if config['show_menu'] else 'CLOSED'}")
                    elif key == "UP":
                        if config.get("show_menu"):
                            config["menu_index"] = (config["menu_index"] - 1) % 4
                    elif key == "DOWN":
                        if config.get("show_menu"):
                            config["menu_index"] = (config["menu_index"] + 1) % 4
                    elif key == "SELECT":
                        if config.get("show_menu"):
                            items = ["Mode", "LightMeter", "Flash", "Grid"]
                            selected = items[config["menu_index"]]
                            print(f"[SYSTEM] Selected: {selected}")
                    
                    time.sleep(max(0, (1.0 / FPS_CAP) - (time.time() - loop_start)))
    except KeyboardInterrupt:
        picam2.stop()

if __name__ == "__main__":
    run()