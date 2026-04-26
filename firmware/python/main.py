import time
import sys
import os
import numpy as np
import mmap
from picamera2 import Picamera2
from PIL import Image, ImageDraw
import subprocess
from UI import ui_top, touch_interface

# Filters
from filters import italian_summer, bokeh, kodak, cyberpunk, nostalgia, low_light
# Settings and Grids
from settings import grid as grid_settings

# Connectivity Utils
from connectivity import wifi_utils
import threading
import json
try:
    import evdev
    from evdev import ecodes
except ImportError:
    evdev = None

# Config
FB_DEVICE = "/dev/fb1" 
SCREEN_RES = (480, 320)
FPS_CAP = 8  # Balanced for smoother preview and SPI stability

picam2 = Picamera2()

class CameraMode:
    def __init__(self, name):
        self.name = name

    def process_frame(self, frame):
        return frame

    def _draw_capture_overlay(self, fb_map, text, progress=0):
        """
        Draws a premium branded capture overlay with a logo and optional progress bar.
        """
        from UI.themes import chalk as theme
        
        w, h = SCREEN_RES
        # Charcoal background instead of pure black
        img = Image.new("RGB", SCREEN_RES, theme.BG_CHARCOAL)
        draw = ImageDraw.Draw(img)
        
        # 1. EuclidCam Logo (Background Watermark)
        cx, cy = w // 2, h // 2 - 30  # Centered for a large background logo
        try:
            # Load the transparent PNG generated from SVG
            logo_path = os.path.join(os.path.dirname(__file__), "../../splashscreen/transparent_logo.png")
            logo = Image.open(logo_path).convert("RGBA")
            # Resize logo to be large and prominent
            logo.thumbnail((250, 250), Image.LANCZOS)
            
            # Reduce opacity to the theme's watermark level
            r, g, b, a = logo.split()
            a = a.point(lambda i: i * theme.LOGO_OPACITY)
            logo = Image.merge('RGBA', (r, g, b, a))
            
            lw, lh = logo.size
            # Paste using the faded alpha mask
            img.paste(logo, (cx - lw // 2, cy - lh // 2), logo)
        except Exception as e:
            # Fallback to simple text if logo not found
            print(f"Could not load logo: {e}")
            try:
                from PIL import ImageFont
                font_logo = ImageFont.truetype(theme.FONT_BOLD, 60)
                draw.text((cx-20, cy-30), "E", fill=(255, 255, 255), font=font_logo)
            except:
                pass

        # 2. Main Text (Massive, Professional font)
        try:
            font_text = ImageFont.truetype(theme.FONT_BOLD, 48)
            tw = draw.textlength(text, font=font_text) if hasattr(draw, "textlength") else len(text) * 25
            # Center the large text nicely
            draw.text(((w - tw) // 2, h // 2 + 20), text, fill=(255, 255, 255), font=font_text)
        except:
            draw.text((w//2 - 80, h//2 + 20), text, fill=(255, 255, 255))

        # 3. Loading Scroll (Progress Bar) - Sleek and wide
        if progress > 0:
            bw, bh = theme.PROGRESS_BAR_WIDTH, theme.PROGRESS_BAR_HEIGHT
            bx, by = (w - bw) // 2, h // 2 + 90
            draw.rectangle([bx, by, bx + bw, by + bh], outline=(80, 80, 100), width=1)
            draw.rectangle([bx, by, bx + int(bw * progress), by + bh], fill=theme.MAUVE_PRIMARY)

        display_to_map(np.array(img), fb_map)

    def capture(self, fb_map, config):
        photo_dir = config.get("photo_dir", ".")
        if not os.path.exists(photo_dir):
            os.makedirs(photo_dir, exist_ok=True)
            
        print(f"\n[SHUTTER] Capturing in {self.name} mode...")
        
        # 1. Visual Feedback: Branded "STAY STILL"
        self._draw_capture_overlay(fb_map, "HOLD STILL")
        
        picam2.stop()
        config_still = picam2.create_still_configuration()
        config_still["controls"] = {
            "Contrast": 1.05,
            "Sharpness": 2.0,
            "AeExposureMode": 1, 
            "AnalogueGain": 4.0 
        }
        picam2.configure(config_still)
        picam2.start()
        
        time.sleep(0.4)
        
        # 2. Shutter Flash
        flash = np.full((SCREEN_RES[1], SCREEN_RES[0], 3), 255, dtype=np.uint8)
        display_to_map(flash, fb_map)
        
        # 3. Processing Feedback: Loading Scroll
        self._draw_capture_overlay(fb_map, "PROCESSING...", progress=0.2)
        
        filename = os.path.join(photo_dir, f"{self.name.lower()}_{int(time.time())}.jpg")
        picam2.capture_file("temp.jpg")
        
        self._draw_capture_overlay(fb_map, "APPLYING VISION...", progress=0.5)
        img = Image.open("temp.jpg").convert("RGB")
        processed_img = self.apply_filter(img)
        
        self._draw_capture_overlay(fb_map, "SAVING...", progress=0.8)
        processed_img.save(filename, quality=95)
        
        # 4. Final Flash to signal end
        self._draw_capture_overlay(fb_map, "DONE!", progress=1.0)
        time.sleep(0.3)
        
        # Review
        review_img = processed_img.resize(SCREEN_RES, Image.LANCZOS)
        display_to_map(np.array(review_img), fb_map)
        time.sleep(1.5)
        
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
        # Preview with filter and 3:2 crop
        img = Image.fromarray(frame)
        
        # Consistent 3:2 crop for preview
        w, h = img.size
        target_ratio = 1.5
        if w / h > target_ratio:
            new_width = h * target_ratio
            img = img.crop(((w - new_width) / 2, 0, (w + new_width) / 2, h))
        else:
            new_height = w / target_ratio
            img = img.crop((0, (h - new_height) / 2, w, (h + new_height) / 2))
        
        img = img.resize(SCREEN_RES, Image.LANCZOS)
            
        if self.filter_func:
            img = self.filter_func(img)
        return np.array(img)

class LowLightMode(CameraMode):
    def __init__(self):
        super().__init__("Low Light")

    def capture(self, fb_map, config):
        photo_dir = config.get("photo_dir", ".")
        if not os.path.exists(photo_dir):
            os.makedirs(photo_dir, exist_ok=True)
            
        print(f"\n[SHUTTER] Capturing in {self.name} mode...")
        
        # 1. Branded Visual Feedback
        self._draw_capture_overlay(fb_map, "HOLD STILL")
        
        picam2.stop()
        config_still = picam2.create_still_configuration()
        
        # Low Light Optimizations - Maximum Sensitivity for speed
        config_still["controls"] = {
            "Contrast": 1.1,
            "Sharpness": 3.0,
            "NoiseReductionMode": 2,
            "AeExposureMode": 1, 
            "AnalogueGain": 8.0 
        }
        
        picam2.configure(config_still)
        picam2.start()
        
        time.sleep(0.5) 
        
        # 2. Shutter Flash
        flash = np.full((SCREEN_RES[1], SCREEN_RES[0], 3), 255, dtype=np.uint8)
        display_to_map(flash, fb_map)
        
        # 3. Processing Feedback: Loading Scroll
        self._draw_capture_overlay(fb_map, "STABILIZING SENSOR...", progress=0.2)
        filename = os.path.join(photo_dir, f"{self.name.lower().replace(' ', '_')}_{int(time.time())}.jpg")
        picam2.capture_file("temp.jpg")
        
        self._draw_capture_overlay(fb_map, "ENHANCING LIGHT...", progress=0.5)
        img = Image.open("temp.jpg").convert("RGB")
        processed_img = self.apply_filter(img)
        
        self._draw_capture_overlay(fb_map, "SAVING RAW...", progress=0.8)
        processed_img.save(filename, quality=95)
        
        # 4. Final signal
        self._draw_capture_overlay(fb_map, "DONE!", progress=1.0)
        time.sleep(0.3)
        
        # Review
        review_img = processed_img.resize(SCREEN_RES, Image.LANCZOS)
        display_to_map(np.array(review_img), fb_map)
        time.sleep(1.5)
        
        picam2.stop()
        start_preview()

    def apply_filter(self, pil_img):
        # Apply 3:2 crop then Low Light filter
        w, h = pil_img.size
        target_ratio = 1.5
        if w / h > target_ratio:
            new_width = h * target_ratio
            img = pil_img.crop(((w - new_width) / 2, 0, (w + new_width) / 2, h))
        else:
            new_height = w / target_ratio
            img = pil_img.crop((0, (h - new_height) / 2, w, (h + new_height) / 2))
        return low_light.apply_low_light_filter(img)

    def process_frame(self, frame):
        # Preview with Low Light filter
        img = Image.fromarray(frame)
        # Consistent 3:2 crop for preview
        w, h = img.size
        target_ratio = 1.5
        if w / h > target_ratio:
            new_width = h * target_ratio
            img = img.crop(((w - new_width) / 2, 0, (w + new_width) / 2, h))
        else:
            new_height = w / target_ratio
            img = img.crop((0, (h - new_height) / 2, w, (h + new_height) / 2))
        
        img = img.resize(SCREEN_RES, Image.LANCZOS)
        img = low_light.apply_low_light_filter(img)
        return np.array(img)

def start_preview():
    config = picam2.create_video_configuration(main={"size": SCREEN_RES, "format": "RGB888"})
    # Subtle Rustic Tuning
    config["controls"] = {
        "Contrast": 1.03,
        "Brightness": 0.02,
        "Sharpness": 1.1
    }
    picam2.configure(config)
    picam2.start()

def display_to_map(data_array, fb_map):
    # Balanced RGB888 to RGB565 (Preserving original B-G-R order for this display)
    data = data_array.astype(np.uint16)
    r = data[:, :, 0] >> 3
    g = (data[:, :, 1] >> 2) << 5
    b = (data[:, :, 2] >> 3) << 11
    
    rgb565 = (r | g | b)
    fb_map[:] = rgb565.tobytes()

def start_server_worker(config):
    # Start server directly
    print("[SYSTEM] Starting Flask server...")
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        cmd = [sys.executable, os.path.join(current_dir, "connectivity/server.py")]
        proc = subprocess.Popen(cmd, cwd=current_dir)
        config["server_proc"] = proc
        config["is_connected"] = True
        config["show_connection_view"] = True
    except Exception as e:
        print(f"[ERROR] Failed to start server: {e}")

def run(config=None):
    if config is None:
        config = {}
        
    config.setdefault("menu_index", 0)
    config.setdefault("submenu_index", 0)
    config.setdefault("show_menu", False)
    config.setdefault("show_submenu", False)
    
    # Handle terminal-based WiFi SSID/Pass
    if len(sys.argv) > 1:
        config["wifi_ssid"] = sys.argv[1]
        if len(sys.argv) > 2:
            config["wifi_pass"] = sys.argv[2]
        print(f"[SYSTEM] WiFi Credentials set via terminal: {config['wifi_ssid']}")

    config.setdefault("wifi_state", None)
    config.setdefault("wifi_state", None)
    config.setdefault("wifi_message", "")
    config.setdefault("grid_mode", "OFF")
    
    modes = [
        StandardMode(),
        WideAngleMode(),
        LowLightMode(),
        FilterMode("Summer", italian_summer),
        FilterMode("Bokeh", bokeh),
        FilterMode("Kodak", kodak),
        FilterMode("Cyberpunk", cyberpunk),
        FilterMode("Nostalgia", nostalgia)
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
    touch = touch_interface.TouchInterface(os.path.join(os.path.dirname(__file__), "UI/touch_settings.json"), SCREEN_RES)
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
                                pil_img = pil_img.resize(SCREEN_RES, Image.LANCZOS)
                                frame = np.array(pil_img)
                            except Exception as e:
                                print(f"[ERROR] Loading {img_path}: {e}")
                                frame = np.zeros((SCREEN_RES[1], SCREEN_RES[0], 3), dtype=np.uint8)
                        else:
                            # Empty gallery
                            frame = np.zeros((SCREEN_RES[1], SCREEN_RES[0], 3), dtype=np.uint8)
                            draw = ImageDraw.Draw(Image.fromarray(frame))
                            draw.text(( SCREEN_RES[0]//2 - 100, SCREEN_RES[1]//2), "Damn Dawg! Thought I was doiing a good job", fill=(255, 255, 255))
                        
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
                    
                    # Process Input (Touch only)
                    key = None
                    touch_cmd = touch.get_touch_command(config)
                    if touch_cmd:
                        if touch_cmd == "TOUCH_SELECT":
                            # Handle direct item selection
                            if not config.get("show_submenu"):
                                config["menu_index"] = config.get("touch_menu_idx", 0) % 4
                            else:
                                config["submenu_index"] = config.get("touch_menu_idx", 0)
                            key = "SELECT"
                        else:
                            key = touch_cmd

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
                                submenu_len = len(modes) if config["current_submenu"] == "Modes" else 3
                                config["submenu_index"] = (config["submenu_index"] - 1) % submenu_len
                    elif key == "DOWN":
                        if config.get("show_menu"):
                            if not config.get("show_submenu"):
                                config["menu_index"] = (config["menu_index"] + 1) % 4
                            else:
                                submenu_len = len(modes) if config["current_submenu"] == "Modes" else 3
                                config["submenu_index"] = (config["submenu_index"] + 1) % submenu_len
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
                    elif key == "BACK" or key == "q":
                        if config.get("show_connection_view"):
                            config["show_connection_view"] = False
                        elif config.get("show_menu"):
                            config["show_menu"] = False
                            config["show_submenu"] = False
                        elif config.get("show_gallery"):
                            config["show_gallery"] = False
                    elif key == "LEFT":
                        if config.get("show_gallery"):
                            config["gallery_idx"] -= 1
                    elif key == "RIGHT":
                        if config.get("show_gallery"):
                            config["gallery_idx"] += 1
                    elif key == "SELECT":
                        if config.get("show_menu"):
                            if not config.get("show_submenu"):
                                items = ["Modes", "Connect", "Flash", "Grid"]
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
                                    if not config.get("is_connected"):
                                        print(f"[SYSTEM] Starting server...")
                                        threading.Thread(target=start_server_worker, args=(config,), daemon=True).start()
                                        config["show_menu"] = False
                                        config["show_submenu"] = False
                                    else:
                                        # Enter submenu to either show QR or Stop
                                        config["show_submenu"] = True
                                        config["current_submenu"] = "Connect"
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
                                elif current_submenu == "Connect":
                                    if config["submenu_index"] == 0:  # Show QR
                                        config["show_connection_view"] = True
                                    elif config["submenu_index"] == 1:  # Stop Connection
                                        print("[SYSTEM] Stopping Flask server...")
                                        proc = config.get("server_proc")
                                        if proc:
                                            proc.terminate()
                                            config["server_proc"] = None
                                        config["is_connected"] = False
                                        config["show_connection_view"] = False
                                    # Option 2 is "Back", just closes submenu
                                
                                config["show_submenu"] = False
                                config["show_menu"] = False # Close menu on select
                    
                    time.sleep(max(0, (1.0 / FPS_CAP) - (time.time() - loop_start)))
    except KeyboardInterrupt:
        if config.get("server_proc"):
            config["server_proc"].terminate()
        picam2.stop()

if __name__ == "__main__":
    run()