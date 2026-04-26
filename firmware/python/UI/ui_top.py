import numpy as np
from PIL import Image, ImageDraw

class TopPanel:
    """
    Handles drawing and rendering of the top-panel UI indicators.
    """
    MAUVE = (224, 176, 255)

    def __init__(self, config, screen_res):
        self.config = config or {}
        self.screen_res = screen_res
        self.padding = self.config.get("ui_padding", 20)
        self.rotation = self.config.get("ui_rotation", 0)

    def _calculate_base_pos(self):
        w, h = self.screen_res
        if self.rotation == 0:
            return w - self.padding, self.padding
        elif self.rotation == 90:
            return w - self.padding, h - self.padding
        elif self.rotation == 180:
            return self.padding, h - self.padding
        else: # 270
            return self.padding, self.padding

    def _draw_flash(self, draw, x_base, y_row):
        if self.config.get("flash"):
            x, y = x_base - 15, y_row - 14
            points = [
                (x, y), (x - 8, y + 8),
                (x - 4, y + 8), (x - 12, y + 20),
                (x - 4, y + 12), (x - 8, y + 12),
                (x, y)
            ]
            draw.polygon(points, fill=self.MAUVE)

    def _draw_battery(self, draw, x_base, y_row):
        x_batt = x_base - 75
        y_batt = y_row - 10
        draw.rectangle([x_batt, y_batt, x_batt + 20, y_batt + 10], outline=self.MAUVE, width=2)
        draw.rectangle([x_batt + 20, y_batt + 3, x_batt + 22, y_batt + 7], fill=self.MAUVE)

    def _draw_wifi(self, draw, x_base, y_row):
        x_wifi = x_base - 115
        y_wifi = y_row - 10
        for i in range(1, 4):
            r = i * 4
            bbox = [x_wifi + 10 - r, y_wifi + 10 - r, x_wifi + 10 + r, y_wifi + 10 + r]
            draw.arc(bbox, 225, 315, fill=self.MAUVE, width=2)

    def _draw_gear(self, draw):
        """
        Draws a small gear icon in the bottom-right corner.
        """
        w, h = self.screen_res
        x, y = w - self.padding - 10, h - self.padding - 10
        draw.ellipse([x-8, y-8, x+8, y+8], outline=self.MAUVE, width=2)
        for i in range(8):
            import math
            angle = i * (360/8)
            x1 = x + 8 * math.cos(math.radians(angle))
            y1 = y + 8 * math.sin(math.radians(angle))
            x2 = x + 12 * math.cos(math.radians(angle))
            y2 = y + 12 * math.sin(math.radians(angle))
            draw.line([x1, y1, x2, y2], fill=self.MAUVE, width=2)

    def _draw_gallery_icon(self, draw):
        """
        Draws a small gallery (picture) icon in the bottom-left corner.
        """
        w, h = self.screen_res
        x, y = self.padding, h - self.padding - 10
        # Draw a small "photo" frame
        draw.rectangle([x, y-12, x+16, y+4], outline=self.MAUVE, width=2)
        # Draw a "mountain" inside
        draw.polygon([(x+3, y+2), (x+8, y-6), (x+13, y+2)], fill=self.MAUVE)
        
        # Highlight if gallery is active
        if self.config.get("show_gallery"):
            draw.text((x + 20, y - 8), "GALLERY", fill=self.MAUVE)

    def _draw_gallery_view(self, draw, gallery_img):
        """
        Draws the gallery viewing state: The image + navigation hints.
        """
        w, h = self.screen_res
        if gallery_img:
            # The gallery_img should already be resized to screen_res or centered
            pass # We'll assume the frame passed to render IS the gallery image if show_gallery is True
        
        # Navigation Hints
        draw.rectangle([10, h-40, 100, h-10], fill=(0, 0, 0, 128))
        draw.text((20, h-35), "[A] Prev", fill=self.MAUVE)
        
        draw.rectangle([w-105, h-40, w-10, h-10], fill=(0, 0, 0, 128))
        draw.text((w-95, h-35), "[D] Next", fill=self.MAUVE)
        
        draw.text((w//2 - 40, h-35), "Exit: [G]", fill=self.MAUVE)

    def _draw_menu(self, draw):
        """
        Draws the settings menu list or a submenu with a Mauve background.
        """
        w, h = self.screen_res
        show_submenu = self.config.get("show_submenu", False)
        current_submenu = self.config.get("current_submenu", "Modes")
        
        if not show_submenu:
            items = ["Modes", "Connect", "Flash", "Grid"]
            selected_idx = self.config.get("menu_index", 0)
            title = "SETTINGS"
        elif current_submenu == "Modes":
            items = ["Standard", "Wide-angle", "Low Light", "Summer", "Bokeh", "Kodak", "Cyberpunk", "Champagne"]
            selected_idx = self.config.get("submenu_index", 0)
            title = "SELECT MODE"
        elif current_submenu == "Grid":
            items = ["OFF", "3x3", "Euclid"]
            selected_idx = self.config.get("submenu_index", 0)
            title = "SELECT GRID"
        elif current_submenu == "Connect":
            items = ["Show QR", "Stop Conn", "Back"]
            selected_idx = self.config.get("submenu_index", 0)
            title = "CONNECT"
        else:
            items = []
            selected_idx = 0
            title = "UNKNOWN"

        # Draw a nearly full-screen semi-transparent overlay
        overlay_margin = 10
        draw.rectangle([overlay_margin, overlay_margin, w - overlay_margin, h - overlay_margin], fill=(0, 0, 0, 200), outline=self.MAUVE, width=3)
        
        # Load a larger font for better visibility
        from PIL import ImageFont
        try:
            font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
            font_item = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
        except:
            font_title = None
            font_item = None

        # Title at the top - Now a giant BACK button
        title_w = draw.textlength(title, font=font_title) if hasattr(draw, "textlength") else len(title) * 14
        draw.text(((w - title_w) // 2, 15), title, fill=self.MAUVE, font=font_title)
        
        # Back Hint
        draw.text((30, 20), "< BACK", fill=self.MAUVE, font=font_item)
        draw.line([(overlay_margin, 60), (w - overlay_margin, 60)], fill=self.MAUVE, width=1)
        
        # Calculate Grid Layout
        num_items = len(items)
        if num_items <= 4:
            # Single row of large buttons
            cols = num_items
            rows = 1
        else:
            # Two rows (for Modes)
            cols = 4
            rows = 2

        btn_w = (w - 40) // cols
        btn_h = (h - 110) // rows
        
        for i, item in enumerate(items):
            row = i // cols
            col = i % cols
            
            bx = 20 + col * btn_w
            by = 80 + row * btn_h
            
            # Button Box
            is_selected = (i == selected_idx)
            # Button Box
            is_selected = (i == selected_idx)
            bg_color = self.MAUVE if is_selected else (40, 40, 40)
            text_color = (0, 0, 0) if is_selected else (255, 255, 255)
            
            # Draw the button with a 15px margin to prevent adjacent taps
            draw.rectangle([bx + 15, by + 15, bx + btn_w - 15, by + btn_h - 15], fill=bg_color, outline=(255, 255, 255) if is_selected else (100, 100, 100), width=2 if is_selected else 1)
            
            # Item Text
            item_text = item
            if item == "Connect":
                status = "ON" if self.config.get("is_connected") else "OFF"
                item_text = f"{item}\n({status})"
            
            # Simple "Icon" markers (positioned relative to button center)
            if item == "Modes": draw.ellipse([bx+btn_w//2-10, by+20, bx+btn_w//2+10, by+40], outline=text_color, width=2)
            elif item == "Flash": draw.polygon([(bx+btn_w//2, by+20), (bx+btn_w//2-10, by+40), (bx+btn_w//2+10, by+40)], outline=text_color, width=2)
            
            # Draw text (handle multi-line for Connect)
            lines = item_text.split('\n')
            for l_idx, line in enumerate(lines):
                tw = draw.textlength(line, font=font_item) if hasattr(draw, "textlength") else len(line) * 10
                draw.text((bx + (btn_w - tw) // 2, by + (btn_h // 2) - 10 + l_idx*20), line, fill=text_color, font=font_item)

    def _draw_bin_icon(self, draw):
        """
        Draws a small trash bin icon in the top-left corner.
        """
        x, y = self.padding, self.padding
        # Draw a simple bin: a rectangle with a lid
        draw.rectangle([x, y+4, x+12, y+16], outline=self.MAUVE, width=2)
        draw.line([(x-2, y+4), (x+14, y+4)], fill=self.MAUVE, width=2)
        draw.rectangle([x+3, y, x+9, y+3], outline=self.MAUVE, width=1)
        # Vertical lines in bin
        draw.line([(x+4, y+8), (x+4, y+14)], fill=self.MAUVE, width=1)
        draw.line([(x+8, y+8), (x+8, y+14)], fill=self.MAUVE, width=1)
        
        draw.text((x + 18, y), "[X] Delete", fill=self.MAUVE)

    def _draw_connection_overlay(self, draw):
        """
        Draws a large QR code and connection details in the center of the screen.
        """
        w, h = self.screen_res
        overlay_w, overlay_h = 300, 240
        x, y = (w - overlay_w) // 2, (h - overlay_h) // 2
        
        # Transparent-ish background box
        draw.rectangle([x, y, x + overlay_w, y + overlay_h], fill=(0, 0, 0), outline=self.MAUVE, width=3)
        
        # Close Button (Top Right of overlay)
        draw.rectangle([x + overlay_w - 40, y + 5, x + overlay_w - 5, y + 30], outline=self.MAUVE, width=2)
        draw.text((x + overlay_w - 32, y + 10), "X", fill=self.MAUVE)

        # Title
        draw.text((x + 20, y + 15), "CONNECTIVITY ACTIVE", fill=self.MAUVE)
        
        # Load the QR code image if it exists
        import os
        qr_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../connectivity/static/qr_code.png"))
        if os.path.exists(qr_path):
            try:
                qr_img = Image.open(qr_path).convert("RGB")
                qr_img = qr_img.resize((140, 140), Image.LANCZOS)
                # Paste it onto the draw surface's image
                draw._image.paste(qr_img, (x + (overlay_w - 140)//2, y + 50))
            except Exception as e:
                print(f"[ERROR] Loading QR for UI: {e}")
                draw.text((x + 20, y + 100), "QR ERROR", fill=(255, 0, 0))
        else:
             draw.text((x + 20, y + 100), "GENERATING QR...", fill=self.MAUVE)

        # Instructions
        draw.text((x + 20, y + overlay_h - 40), "Scan to browse images", fill=self.MAUVE)
        draw.text((x + 20, y + overlay_h - 20), "Tap [X] or edges to close", fill=self.MAUVE)

    def render(self, frame):
        """
        Applies the UI overlay to the provided frame.
        """
        img = Image.fromarray(frame)
        draw = ImageDraw.Draw(img)
        
        show_gallery = self.config.get("show_gallery", False)
        
        if show_gallery:
            self._draw_bin_icon(draw)
            self._draw_gallery_view(draw, None)
        elif self.config.get("show_connection_view", False):
            draw._image = img 
            self._draw_connection_overlay(draw)
        else:
            x_base, y_base = self._calculate_base_pos()
            y_row = y_base + 5
            
            self._draw_flash(draw, x_base, y_row)
            self._draw_battery(draw, x_base, y_row)
            self._draw_wifi(draw, x_base, y_row)
            
            self._draw_gear(draw)
            self._draw_gallery_icon(draw)
            
            if self.config.get("show_menu"):
                self._draw_menu(draw)

        return np.array(img)
