import os
import json

try:
    import evdev
    from evdev import ecodes
except ImportError:
    evdev = None

class TouchInterface:
    def __init__(self, config_path, screen_res):
        self.device = self._find_touch_device()
        self.config = self._load_config(config_path)
        self.screen_res = screen_res
        self.last_x = 0
        self.last_y = 0
        self.touch_active = False

    def _find_touch_device(self):
        if not evdev: return None
        try:
            devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
            for dev in devices:
                if "touchscreen" in dev.name.lower() or "ads7846" in dev.name.lower():
                    return dev
        except:
            pass
        return None

    def _load_config(self, path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except:
            return None

    def get_touch_command(self, ui_state):
        if not self.device or not self.config: return None
        
        try:
            while True: # Drain the event queue
                event = self.device.read_one()
                if event is None: break
                
                if event.type == ecodes.EV_ABS:
                    if event.code == ecodes.ABS_X: self.last_x = event.value
                    if event.code == ecodes.ABS_Y: self.last_y = event.value
                elif event.type == ecodes.EV_KEY and event.code == ecodes.BTN_TOUCH:
                    if event.value == 1: # Touch start
                        self.touch_active = True
                    else: # Touch release
                        self.touch_active = False
                        return self._map_to_command(self.last_x, self.last_y, ui_state)
        except Exception as e:
            pass
        return None

    def _map_to_command(self, raw_x, raw_y, ui_state):
        # Map raw to screen
        c = self.config
        x = (raw_x - c["x_min"]) / (c["x_max"] - c["x_min"]) * c["screen_width"]
        y = (raw_y - c["y_min"]) / (c["y_max"] - c["y_min"]) * c["screen_height"]
        
        if c.get("invert_x"): x = c["screen_width"] - x
        if c.get("invert_y"): y = c["screen_height"] - y
        
        # Hitboxes
        w, h = self.screen_res

        # 1. Menu Toggle (Bottom Right)
        if x > w - 60 and y > h - 60:
            return "SPACE"
        
        # 2. Gallery Toggle (Bottom Left)
        if x < 60 and y > h - 60:
            return "GALLERY"

        # 3. Mode Selection / Menu Interaction
        if ui_state.get("show_menu"):
            # Close menu if clicking outside
            menu_w, menu_h = 240, 220
            menu_x, menu_y = (w - menu_w) // 2, (h - menu_h) // 2
            if x < menu_x or x > menu_x + menu_w or y < menu_y or y > menu_y + menu_h:
                return "BACK"
            
            # Click items
            rel_y = y - (menu_y + 28)
            if 0 <= rel_y <= 175: # Approx 7 items * 25px
                idx = int(rel_y // 25)
                ui_state["touch_menu_idx"] = idx
                return "TOUCH_SELECT"

        # 4. Gallery Mode
        if ui_state.get("show_gallery"):
            if x < 60 and y < 60: # Delete icon (Top Left)
                return "DOWN" 
            if y < 60: # Top bar back
                return "BACK"
            if x < w // 2:
                return "LEFT"
            else:
                return "RIGHT"

        # 5. Capture (Center of screen when no menu/gallery)
        if not ui_state.get("show_menu") and not ui_state.get("show_gallery"):
            return "ENTER"

        return None
