# PyPortal Adafruit IO Appliance
# Brent Rubell for Adafruit Industries, 2020
import time
import board
import neopixel
import displayio
import terminalio
import adafruit_touchscreen
import adafruit_bitmap_font
from adafruit_button import Button
from adafruit_bitmap_font import bitmap_font
from adafruit_pyportal import PyPortal
from adafruit_display_text import label

pyportal = PyPortal()
display = board.DISPLAY
display.rotation = 90
# Set the backlight
pyportal.set_backlight(0.3)
# Rotate touchscreen to 90 degrees
screen_height = 320
screen_width = 240
ts = adafruit_touchscreen.Touchscreen(board.TOUCH_YU, board.TOUCH_YD,
                                      board.TOUCH_XL, board.TOUCH_XR, 
                                      calibration=((5200, 59000), (5800, 57000)),
                                      size=(screen_height, screen_width))

# Display Groups
splash = displayio.Group(max_size=15)  # Primary group
view_ui = displayio.Group(max_size=15) # Group for UI View Objects
splash.append(view_ui)


# --- Display Text --- #
# Set up fonts
font_temp_main = bitmap_font.load_font("/fonts/Helvetica-Bold-100.bdf")
font_temp_main.load_glyphs(b'abcdefghjiklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890- ()')

font_text = bitmap_font.load_font("/fonts/Helvetica-Bold-44.bdf")
font_text.load_glyphs(b'abcdefghjiklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890- ()')

# Label to hold sensor temperature value
lbl_temperature = label.Label(font_temp_main, text="63F", color=0xFFFFFF)
lbl_temperature.x = int(screen_width/7)
lbl_temperature.y = int(screen_height/5)
view_ui.append(lbl_temperature)

# Label to hold preset temperature value
lbl_temp_set = label.Label(font_text, text="Set: 60F", color=0xFFFFFF)
lbl_temp_set.x = int(screen_width/7)
lbl_temp_set.y = int(screen_height/2)
view_ui.append(lbl_temp_set)

# --- Display Buttons --- #
# Default button styling:
BUTTON_HEIGHT = 40
BUTTON_WIDTH = 80

# Large buttons at the bottom of the display
BIG_BUTTON_HEIGHT = int(screen_height/3.2)
BIG_BUTTON_WIDTH = int(screen_width/2)
BIG_BUTTON_Y = int(screen_height-BIG_BUTTON_HEIGHT)

buttons = []

button_dec = Button(name="button_dec", x=0, y=BIG_BUTTON_Y,
                       width=BIG_BUTTON_WIDTH, height=BIG_BUTTON_HEIGHT,
                       label="-", label_font=font_text, label_color=0xFFFFFF,
                       fill_color=0x008FF, outline_color=0x767676,
                       selected_fill=0x1a1a1a, selected_outline=0x2e2e2e,
                       selected_label=0x525252)
view_ui.append(button_dec)  # add this button to the ui group
buttons.append(button_dec)

button_inc = Button(name="button_inc", x=BIG_BUTTON_WIDTH, y=BIG_BUTTON_Y,
                  width=BIG_BUTTON_WIDTH, height=BIG_BUTTON_HEIGHT,
                  label="+", label_font=font_text, label_color=0xFFFFFF,
                  fill_color=0xff4000, outline_color=0x767676,
                  selected_fill=0x1a1a1a, selected_outline=0x2e2e2e,
                  selected_label=0x525252)
view_ui.append(button_inc)  # add this button to the ui group
buttons.append(button_inc)

display.show(splash)

last_pressed = None
currently_pressed = None
while True:
    p = pyportal.touchscreen.touch_point
    if p:
        print(p)
        for b in buttons:
            if b.contains(p):
                print("Touched", b.name)
                currently_pressed = b
                break
        else:
            currently_pressed = None
    time.sleep(0.05)