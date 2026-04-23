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
        # Simple gear: a circle with some teeth
        draw.ellipse([x-8, y-8, x+8, y+8], outline=self.MAUVE, width=2)
        for i in range(8):
            angle = i * (360/8)
            # Draw small teeth (lines)
            from math import cos, sin, radians
            x1 = x + 8 * cos(radians(angle))
            y1 = y + 8 * sin(radians(angle))
            x2 = x + 12 * cos(radians(angle))
            y2 = y + 12 * sin(radians(angle))
            draw.line([x1, y1, x2, y2], fill=self.MAUVE, width=2)

    def _draw_menu(self, draw):
        """
        Draws the settings menu list with a Mauve background.
        """
        w, h = self.screen_res
        menu_w, menu_h = 150, 120
        x, y = (w - menu_w) // 2, (h - menu_h) // 2
        
        # Mauve background box
        draw.rectangle([x, y, x + menu_w, y + menu_h], fill=self.MAUVE)
        
        # Menu items
        items = ["Mode", "LightMeter", "Flash", "Grid"]
        for i, item in enumerate(items):
            # Drawing text is tricky without a font, but we'll use rectangles as placeholders
            # or try to find a default font. 
            # For now, we'll draw simple text placeholders if no font is available.
            draw.text((x + 10, y + 10 + i*25), item, fill=(0, 0, 0))

    def render(self, frame):
        """
        Applies the UI overlay to the provided frame.
        """
        img = Image.fromarray(frame)
        draw = ImageDraw.Draw(img)
        
        x_base, y_base = self._calculate_base_pos()
        y_row = y_base + 5
        
        self._draw_flash(draw, x_base, y_row)
        self._draw_battery(draw, x_base, y_row)
        self._draw_wifi(draw, x_base, y_row)
        
        # Bottom-right gear
        self._draw_gear(draw)
        
        # Settings menu
        if self.config.get("show_menu"):
            self._draw_menu(draw)

        return np.array(img)
