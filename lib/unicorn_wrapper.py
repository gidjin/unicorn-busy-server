#!/usr/bin/env python
import contextlib
import io
import colorsys

try:
    import spidev
    import unicornhat
    from unicornhatmini import UnicornHATMini
    HARDWARE_AVAILABLE = True
except ImportError:
    HARDWARE_AVAILABLE = False
    print("Hardware libraries not available. Running in mock mode.")


class DummyHat:
    """Mock Unicorn HAT for testing without hardware"""
    def __init__(self):
        self.width = 8
        self.height = 4
        self.brightness_value = 0.5
        self.pixels = {}
        self.rotation_value = 0
        print("🦄 DummyHat initialized (8x4 grid)")

    def get_shape(self):
        return (self.width, self.height)

    def set_brightness(self, brightness):
        self.brightness_value = brightness

    def brightness(self, brightness):
        self.set_brightness(brightness)

    def get_brightness(self):
        return self.brightness_value

    def set_rotation(self, rotation):
        self.rotation_value = rotation
        print(f"🔄 Rotation set to: {rotation}°")

    def rotation(self, rotation):
        self.set_rotation(rotation)

    def set_layout(self, layout):
        print(f"📐 Layout set")

    def clear(self):
        self.pixels = {}
        print("🧹 Display cleared")

    def set_pixel(self, x, y, r, g, b):
        self.pixels[(x, y)] = (r, g, b)

    def set_all(self, r, g, b):
        for x in range(self.width):
            for y in range(self.height):
                self.pixels[(x, y)] = (r, g, b)

    def show(self):
        if not self.pixels:
            print("💡 Display: [OFF]")
            return

        # Get the dominant color (most common)
        colors = list(self.pixels.values())
        if colors:
            # Use the first pixel's color as representative
            r, g, b = colors[0]
            color_name = self._get_color_name(r, g, b)

            # Only print status colors prominently (not rainbow animations)
            if color_name in ["GREEN (Available)", "RED (Busy)", "YELLOW (Away)", "BLACK/OFF"]:
                print(f"💡 Display: RGB({r}, {g}, {b}) - {color_name}")
                print(f"🔆 Brightness set to: {self.brightness_value}")

    def _get_color_name(self, r, g, b):
        """Convert RGB to a human-readable color name"""
        if r == 0 and g == 0 and b == 0:
            return "BLACK/OFF"
        elif r == 0 and g == 144 and b == 0:
            return "GREEN (Available)"
        elif r == 179 and g == 0 and b == 0:
            return "RED (Busy)"
        elif r == 255 and g == 191 and b == 0:
            return "YELLOW (Away)"
        elif r > 200 and g > 200 and b > 200:
            return "WHITE"
        elif r > g and r > b:
            return "RED"
        elif g > r and g > b:
            return "GREEN"
        elif b > r and b > g:
            return "BLUE"
        elif r > 200 and g > 200:
            return "YELLOW"
        elif r > 200 and b > 200:
            return "MAGENTA"
        elif g > 200 and b > 200:
            return "CYAN"
        else:
            return "MIXED"

class UnicornWrapper:
    def __init__(self, hat = None):
        # If hardware libraries aren't available, force dummy mode
        if not HARDWARE_AVAILABLE:
            hat = 'dummy'

        if hat is None:
            try:
                spidev.SpiDev(0,0)
                hat = 'mini'
            except FileNotFoundError:
                hat = 'phat'

        if hat == 'mini':
            self.hat = UnicornHATMini()
            self.type = hat
            self.hat.set_brightness(0.5)
            self.hat.set_rotation(90)
        elif hat == 'dummy' or not HARDWARE_AVAILABLE:
            self.hat = DummyHat()
            self.type = 'dummy'
        else:
            self.hat = unicornhat
            self.type = hat
            self.hat.set_layout(unicornhat.PHAT)
            self.hat.brightness(0.5)
            self.hat.rotation(90)
        self.brightness = 0.5
        self.rotation = 0
        self.width, self.height = self.hat.get_shape()

    def getType(self):
        return self.type

    def getHat(self):
        return self.hat

    def clear(self):
        return self.hat.clear()

    def getShape(self):
        return self.hat.get_shape()

    def setAll(self, r, g, b):
        self.hat.set_all(r, g, b)

    def getBrightness(self):
        if self.type == 'phat':
            return self.hat.get_brightness()
        
        return self.brightness
    
    def setBrightness(self, brightness):
        self.brightness = brightness

        if self.type == 'phat':
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                self.hat.brightness(brightness)
        elif self.type == 'mini':
            self.hat.set_brightness(brightness)
        elif self.type == 'dummy':
            self.hat.set_brightness(brightness)

    def setPixel(self, x, y, r, g, b):
        self.hat.set_pixel(x, y, r, g, b)
    
    def setColour(self, r = None, g = None, b = None, RGB = None):
        if RGB is not None:
            r = RGB[0]
            g = RGB[1]
            b = RGB[2] 
        self.hat.clear()
        for x in range(self.width):
            for y in range(self.height):
                self.setPixel(x, y, r, g, b)
        self.hat.show()
    
    def setRotation(self, r=0):
        if self.type == 'phat':
            self.hat.rotation(r)
        elif self.type == 'mini':
            self.hat.set_rotation(r)
        elif self.type == 'dummy':
            self.hat.set_rotation(r)
        self.rotation = r
    
    def getRotation(self):
        return self.rotation
    
    def show(self):
        self.hat.show()

    def off(self):
        self.hat.clear()
        self.hat.show()
    
    # Colour converstion operations as we only understand RGB
    def hsvIntToRGB(self, h, s, v):
        h = h / 360
        s = s /100
        v = v / 100
        return tuple(round(i * 255) for i in colorsys.hsv_to_rgb(h,s,v))
    
    def htmlToRGB(self, html):
        if len(html) is 6:
            r = int(f"{html[0]}{html[1]}", 16)
            g = int(f"{html[2]}{html[3]}", 16)
            b = int(f"{html[4]}{html[5]}", 16)
        elif len(html) > 6:
            r = int(f"{html[1]}{html[2]}", 16)
            g = int(f"{html[3]}{html[4]}", 16)
            b = int(f"{html[5]}{html[6]}", 16)
        else:
            raise Exception("The Hex value is not in the correct format it should RRGGBB or #RRGGBB the same as HTML")
        return tuple(r,g,b)
