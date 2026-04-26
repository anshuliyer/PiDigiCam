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
                        cmd, x, y = self._map_to_command(self.last_x, self.last_y, ui_state)
                        if cmd:
                            print(f"[TOUCH] {cmd} at ({int(x)}, {int(y)})")
                        return cmd
        except Exception as e:
            pass
        return None

    def _map_to_command(self, raw_x, raw_y, ui_state):
        c = self.config
        
        # 1. Swap axes if necessary
        if c.get("swap_xy"):
            raw_x, raw_y = raw_y, raw_x
            
        # 2. Map raw to screen coordinates (0 to 1 range)
        x_norm = (raw_x - c["x_min"]) / (c["x_max"] - c["x_min"])
        y_norm = (raw_y - c["y_min"]) / (c["y_max"] - c["y_min"])
        
        # 3. Invert if necessary
        if c.get("invert_x"): x_norm = 1.0 - x_norm
        if c.get("invert_y"): y_norm = 1.0 - y_norm
        
        # 4. Scale to screen resolution
        x = x_norm * self.screen_res[0]
        y = y_norm * self.screen_res[1]
        
        # Hitboxes
        w, h = self.screen_res

        # 1. Menu Toggle (Bottom Right - Gear Icon)
        if x > w - 85 and y > h - 85:
            return "SPACE", x, y
        
        # 2. Gallery Toggle (Bottom Left - Picture Icon)
        if x < 85 and y > h - 85:
            return "GALLERY", x, y

        # 3. Grid Menu Interaction
        if ui_state.get("show_menu"):
            # 1. Back/Close Button Area (Top 80px or very edges)
            if y < 80 or x < 10 or x > w - 10 or y > h - 10:
                return "BACK", x, y
            
            # Determine grid dims
            sub = ui_state.get("current_submenu")
            is_sub = ui_state.get("show_submenu")
            
            if is_sub and sub == "Modes":
                max_items, cols, rows = 8, 4, 2
            elif is_sub and (sub == "Grid" or sub == "Connect"):
                max_items, cols, rows = 3, 3, 1
            else: # Main Menu
                max_items, cols, rows = 4, 4, 1
                
            btn_w = (w - 40) // cols
            btn_h = (h - 100) // rows
            
            # Calculate clicked col/row
            rel_x = x - 20
            rel_y = y - 80 # Adjusted for larger back area
            
            col = int(rel_x // btn_w)
            row = int(rel_y // btn_h)
            
            if 0 <= col < cols and 0 <= row < rows:
                # Calculate internal button coordinates to check for margins
                btn_local_x = rel_x % btn_w
                btn_local_y = rel_y % btn_h
                
                # Increased dead-zone to 15px to prevent adjacent merging
                if 15 < btn_local_x < btn_w - 15 and 15 < btn_local_y < btn_h - 15:
                    idx = row * cols + col
                    if idx < max_items:
                        ui_state["touch_menu_idx"] = idx
                        return "TOUCH_SELECT", x, y

        # 4. Connection Overlay Close
        if ui_state.get("show_connection_view"):
            overlay_w, overlay_h = 300, 240
            ox, oy = (w - overlay_w) // 2, (h - overlay_h) // 2
            # Close button area (Top Right of overlay) or tapping outside
            if (x > ox + overlay_w - 50 and y < oy + 50) or (x < ox or x > ox + overlay_w or y < oy or y > oy + overlay_h):
                return "BACK", x, y

        # 5. Gallery Mode
        if ui_state.get("show_gallery"):
            if x < 85 and y < 85: # Delete icon (Top Left)
                return "DOWN", x, y 
            if y < 70: # Top bar back
                return "BACK", x, y
            if x < w // 2:
                return "LEFT", x, y
            else:
                return "RIGHT", x, y

        # 6. Capture (Center of screen when no menu/gallery/connection)
        if not ui_state.get("show_menu") and not ui_state.get("show_gallery") and not ui_state.get("show_connection_view"):
            # Central area (Avoid edges where icons are)
            if 80 < x < w - 80 and 80 < y < h - 80:
                return "ENTER", x, y

        return None, x, y
