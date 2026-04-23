import time
import sys
import select
import os
import numpy as np
import mmap
from picamera2 import Picamera2
from PIL import Image, ImageDraw
import subprocess
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
    config.setdefault("mode_idx", 0)
    config.setdefault("grid_mode", grid_settings.CompositionGrid.OFF)
    config.setdefault("show_gallery", False)
    config.setdefault("gallery_idx", 0)
    config.setdefault("photo_dir", "../../Captured")
    config.setdefault("is_connected", False)
    config.setdefault("server_proc", None)
    
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
                    
                    if config.get("show_gallery"):
                        # Gallery Mode: Load and display captured image
                        photo_dir = config.get("photo_dir", "../../Captured")
                        if not os.path.exists(photo_dir):
                            os.makedirs(photo_dir, exist_ok=True)
                        
                        files = sorted([f for f in os.listdir(photo_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
                        if files:
                            idx = config["gallery_idx"] % len(files)
                            img_path = os.path.join(photo_dir, files[idx])
                            try:
                                pil_img = Image.open(img_path).convert("RGB")
                                pil_img = pil_img.resize(SCREEN_RES)
                                frame = np.array(pil_img)
                            except Exception as e:
                                print(f"[ERROR] Loading {img_path}: {e}")
                                frame = np.zeros((SCREEN_RES[1], SCREEN_RES[0], 3), dtype=np.uint8)
                        else:
                            # Empty gallery
                            frame = np.zeros((SCREEN_RES[1], SCREEN_RES[0], 3), dtype=np.uint8)
                            draw = ImageDraw.Draw(Image.fromarray(frame))
                            draw.text(( SCREEN_RES[0]//2 - 40, SCREEN_RES[1]//2), "Captured is Empty", fill=(255, 255, 255))
                        
                        frame = panel.render(frame)
                        display_to_map(frame, fb_map)
                    else:
                        # Camera Mode
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
                        elif config.get("show_gallery"):
                            # Delete logic for gallery (X key)
                            photo_dir = config.get("photo_dir", "../../Captured")
                            files = sorted([f for f in os.listdir(photo_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
                            if files:
                                idx = config["gallery_idx"] % len(files)
                                img_path = os.path.join(photo_dir, files[idx])
                                try:
                                    print(f"[SYSTEM] Deleting {img_path}...")
                                    os.remove(img_path)
                                    # Refresh list and adjust idx
                                    files.pop(idx)
                                    if not files:
                                        config["gallery_idx"] = 0
                                    else:
                                        config["gallery_idx"] = idx % len(files)
                                except Exception as e:
                                    print(f"[ERROR] Deleting file: {e}")
                    elif key == "GALLERY":
                        config["show_gallery"] = not config.get("show_gallery", False)
                        config["show_menu"] = False
                        if config["show_gallery"]:
                            config["gallery_idx"] = 0 # Reset to latest or first
                    elif key == "LEFT":
                        if config.get("show_gallery"):
                            config["gallery_idx"] -= 1
                    elif key == "RIGHT":
                        if config.get("show_gallery"):
                            config["gallery_idx"] += 1
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
                                elif selected == "Connect":
                                    # Toggle Flask Server
                                    if not config.get("is_connected"):
                                        print("[SYSTEM] Starting Flask server...")
                                        try:
                                            # Run from our directory
                                            cmd = [sys.executable, "connectivity/server.py"]
                                            proc = subprocess.Popen(cmd, cwd=os.path.dirname(__file__))
                                            config["server_proc"] = proc
                                            config["is_connected"] = True
                                        except Exception as e:
                                            print(f"[ERROR] Failed to start server: {e}")
                                    else:
                                        print("[SYSTEM] Stopping Flask server...")
                                        proc = config.get("server_proc")
                                        if proc:
                                            proc.terminate()
                                            config["server_proc"] = None
                                        config["is_connected"] = False
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
        if config.get("server_proc"):
            config["server_proc"].terminate()
        picam2.stop()

if __name__ == "__main__":
    run()