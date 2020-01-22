import time

from adafruit_esp32spi import adafruit_esp32spi
from adafruit_display_text.label import Label
from adafruit_bitmap_font import bitmap_font
import adafruit_imageload
import board
import busio
import displayio
from adafruit_pyportal import PyPortal
from digitalio import DigitalInOut

# Background image
BACKGROUND = "/images/roots.bmp"
# Icons for water level and temperature
ICON_LEVEL = "/images/icon-wetness.bmp"
ICON_TEMP = "/images/icon-temp.bmp"
# Water color
WATER_COLOR = 0x0099ff

# the current working directory (where this file is)
cwd = ("/"+__file__).rsplit('/', 1)[0]

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

# PyPortal ESP32 AirLift Pins
esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)
 
# Initialize PyPortal's ESP32
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

# Initialize PyPortal Display
display = board.DISPLAY
 
WIDTH = board.DISPLAY.width
HEIGHT = board.DISPLAY.height

# TODO: remove this!
print(WIDTH, HEIGHT)

# Initialize new PyPortal object
pyportal = PyPortal(esp=esp,
                    external_spi=spi)

# Create a new DisplayIO group
splash = displayio.Group(max_size=15)

# Load background image
try:
    bg_bitmap, bg_palette = adafruit_imageload.load(BACKGROUND,
                                                    bitmap=displayio.Bitmap,
                                                    palette=displayio.Palette)
# Or just use solid color
except (OSError, TypeError):
    BACKGROUND = BACKGROUND if isinstance(BACKGROUND, int) else 0x000000
    bg_bitmap = displayio.Bitmap(display.width, display.height, 1)
    bg_palette = displayio.Palette(1)
    bg_palette[0] = BACKGROUND
background = displayio.TileGrid(bg_bitmap, pixel_shader=bg_palette)

# Add background to display
splash.append(background)

# Load icons for wetness and temperature
icon_tmp_bitmap, icon_palette = adafruit_imageload.load(ICON_TEMP,
                                                bitmap=displayio.Bitmap,
                                                palette=displayio.Palette)
icon_tmp_bitmap = displayio.TileGrid(icon_tmp_bitmap,
                                      pixel_shader=icon_palette,
                                      x=0, y=280)

icon_lvl_bitmap, icon_palette = adafruit_imageload.load(ICON_LEVEL,
                                                bitmap=displayio.Bitmap,
                                                palette=displayio.Palette)
icon_lvl_bitmap = displayio.TileGrid(icon_lvl_bitmap,
                                      pixel_shader=icon_palette,
                                      x=345, y=280)

# Add icons to display
splash.append(icon_tmp_bitmap)
splash.append(icon_lvl_bitmap)

# Palette for water bitmap
palette = displayio.Palette(2)
palette[0] = 0x000000
palette[1] = WATER_COLOR
palette.make_transparent(0)

water_bmp = displayio.Bitmap(display.width, display.height, len(palette))
water = displayio.TileGrid(water_bmp, pixel_shader=palette)
splash.append(water)

print('loading font...')
# Fonts within /fonts/ folder
font = cwd+"/fonts/GothamBlack-50.bdf"

glyphs = b'0123456789FC-° '
font = bitmap_font.load_font(font)
font.load_glyphs(glyphs)

# Create a label to display the temperature
label_temp = Label(font, max_glyphs=4)
label_temp.x = 35
label_temp.y = 300
splash.append(label_temp)

# Create a label to display the water level
label_level = Label(font, max_glyphs=4)
label_level.x = display.width - 95
label_level.y = 300
splash.append(label_level)

# TODO: remove this...
label_temp.text = "272F"
label_level.text = "52"

# show displayio splash group
display.show(splash)

"""
# Add water to planter
print("filling")
print("height: ", HEIGHT)
for x in range(0, WIDTH-1):
  for y in range(100, 200):
    water_bmp[x, y] = 1
print("filled")
"""

while True:
  pass
