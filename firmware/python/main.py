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

# Filters
from filters import italian_summer, bokeh, kodak, cyberpunk, champagne
# Settings and Grids
from settings import grid as grid_settings

# Config
FB_DEVICE = "/dev/fb1" 
SCREEN_RES = (480, 320)
FPS_CAP = 3  # Keeps SPI bus stable

picam2 = Picamera2()

class CameraMode:
    def __init__(self, name):
        self.name = name

    def process_frame(self, frame):
        return frame

    def capture(self, fb_map, config):
        photo_dir = config.get("photo_dir", ".")
        if not os.path.exists(photo_dir):
            os.makedirs(photo_dir, exist_ok=True)
            
        print(f"\n[SHUTTER] Capturing in {self.name} mode...")
        picam2.stop()
        config_still = picam2.create_still_configuration()
        picam2.configure(config_still)
        picam2.start()
        
        time.sleep(1)
        filename = os.path.join(photo_dir, f"{self.name.lower()}_{int(time.time())}.jpg")
        picam2.capture_file("temp.jpg")
        
        img = Image.open("temp.jpg").convert("RGB")
        processed_img = self.apply_filter(img)
        processed_img.save(filename, quality=95)
        
        # Review
        review_img = processed_img.resize(SCREEN_RES)
        display_to_map(np.array(review_img), fb_map)
        time.sleep(2.0)
        
        picam2.stop()
        start_preview()

    def apply_filter(self, pil_img):
        return pil_img

class StandardMode(CameraMode):
    def __init__(self):
        super().__init__("Standard")

    def apply_filter(self, pil_img):
        # 3:2 Cropping logic from normal.py
        w, h = pil_img.size
        target_ratio = 1.5
        if w / h > target_ratio:
            new_width = h * target_ratio
            left = (w - new_width) / 2
            right = (w + new_width) / 2
            return pil_img.crop((left, 0, right, h))
        else:
            new_height = w / target_ratio
            top = (h - new_height) / 2
            bottom = (h + new_height) / 2
            return pil_img.crop((0, top, w, bottom))

    def process_frame(self, frame):
        # Standard mode now relies on the global toggleable grid
        return frame

class WideAngleMode(CameraMode):
    def __init__(self):
        super().__init__("Wide-angle")
    # Wide-angle: do nothing as requested.

class FilterMode(CameraMode):
    def __init__(self, name, filter_module):
        super().__init__(name)
        self.filter_module = filter_module
        # Find the filter function (e.g., apply_bokeh_filter)
        self.filter_func = None
        for attr in dir(filter_module):
            if attr.startswith("apply_") and attr.endswith("_filter"):
                self.filter_func = getattr(filter_module, attr)
                break

    def apply_filter(self, pil_img):
        # Apply 3:2 crop first, then filter
        w, h = pil_img.size
        target_ratio = 1.5
        if w / h > target_ratio:
            new_width = h * target_ratio
            img = pil_img.crop(((w - new_width) / 2, 0, (w + new_width) / 2, h))
        else:
            new_height = w / target_ratio
            img = pil_img.crop((0, (h - new_height) / 2, w, (h + new_height) / 2))
        
        if self.filter_func:
            return self.filter_func(img)
        return img

    def process_frame(self, frame):
        # Preview with filter
        img = Image.fromarray(frame)
        if self.filter_func:
            img = self.filter_func(img)
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

def run(config=None):
    if config is None:
        config = {}
        
    config.setdefault("menu_index", 0)
    config.setdefault("submenu_index", 0)
    config.setdefault("show_menu", False)
    config.setdefault("show_submenu", False)
    
    modes = [
        StandardMode(),
        WideAngleMode(),
        FilterMode("Summer", italian_summer),
        FilterMode("Bokeh", bokeh),
        FilterMode("Kodak", kodak),
        FilterMode("Cyberpunk", cyberpunk),
        FilterMode("Champagne", champagne)
    ]
    config.setdefault("grid_mode", grid_settings.CompositionGrid.OFF)
    comp_grid = grid_settings.CompositionGrid()
    
    panel = ui_top.TopPanel(config, SCREEN_RES)
    kbd = io_stubs.KeyboardInterface()
    start_preview()
    
    try:
        with open(FB_DEVICE, "r+b") as f:
            map_size = SCREEN_RES[0] * SCREEN_RES[1] * 2
            with mmap.mmap(f.fileno(), map_size) as fb_map:
                while True:
                    loop_start = time.time()
                    current_mode = modes[config["mode_idx"]]
                    
                    frame = picam2.capture_array()
                    if frame is not None:
                        frame = current_mode.process_frame(frame)
                        
                        # Apply Compositional Grid if enabled
                        pil_img = Image.fromarray(frame)
                        pil_img = comp_grid.apply(pil_img, config["grid_mode"])
                        frame = np.array(pil_img)
                        
                        frame = panel.render(frame)
                        display_to_map(frame, fb_map)
                    
                    key = kbd.get_input()
                    if key == "ENTER":
                        current_mode.capture(fb_map, config)
                    elif key == "SPACE":
                        config["show_menu"] = not config.get("show_menu", False)
                        config["show_submenu"] = False # Reset submenu on toggle
                    elif key == "UP":
                        if config.get("show_menu"):
                            if not config.get("show_submenu"):
                                config["menu_index"] = (config["menu_index"] - 1) % 4
                            else:
                                config["submenu_index"] = (config["submenu_index"] - 1) % len(modes)
                    elif key == "DOWN":
                        if config.get("show_menu"):
                            if not config.get("show_submenu"):
                                config["menu_index"] = (config["menu_index"] + 1) % 4
                            else:
                                config["submenu_index"] = (config["submenu_index"] + 1) % len(modes)
                    elif key == "SELECT":
                        if config.get("show_menu"):
                            if not config.get("show_submenu"):
                                items = ["Modes", "LightMeter", "Flash", "Grid"]
                                selected = items[config["menu_index"]]
                                if selected == "Modes":
                                    config["show_submenu"] = True
                                    config["current_submenu"] = "Modes"
                                    config["submenu_index"] = config.get("mode_idx", 0)
                                elif selected == "Grid":
                                    config["show_submenu"] = True
                                    config["current_submenu"] = "Grid"
                                    # Find current grid index
                                    grid_options = ["OFF", "3x3", "Euclid"]
                                    try:
                                        config["submenu_index"] = grid_options.index(config["grid_mode"])
                                    except ValueError:
                                        config["submenu_index"] = 0
                                elif selected == "Flash":
                                    config["flash"] = not config.get("flash", False)
                            else:
                                current_submenu = config.get("current_submenu")
                                if current_submenu == "Modes":
                                    config["mode_idx"] = config["submenu_index"]
                                    print(f"[SYSTEM] Mode changed to {modes[config['mode_idx']].name}")
                                elif current_submenu == "Grid":
                                    grid_options = ["OFF", "3x3", "Euclid"]
                                    config["grid_mode"] = grid_options[config["submenu_index"]]
                                    print(f"[SYSTEM] Grid changed to {config['grid_mode']}")
                                
                                config["show_submenu"] = False
                                config["show_menu"] = False # Close menu on select
                    
                    time.sleep(max(0, (1.0 / FPS_CAP) - (time.time() - loop_start)))
    except KeyboardInterrupt:
        picam2.stop()

if __name__ == "__main__":
    run()