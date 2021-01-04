# CircuitPython Google OAuth
# for PyPortal
import time
import board
import busio
from digitalio import DigitalInOut
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from adafruit_esp32spi import adafruit_esp32spi
import adafruit_requests as requests
import displayio
from adafruit_display_text.label import Label
from adafruit_bitmap_font import bitmap_font
import adafruit_miniqr

# Add a secrets.py to your filesystem that has a dictionary called secrets with "ssid" and
# "password" keys with your WiFi credentials. DO NOT share that file or commit it into Git or other
# source control.
# pylint: disable=no-name-in-module,wrong-import-order
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

# If you are using a board with pre-defined ESP32 Pins:
esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)

# If you have an externally connected ESP32:
# esp32_cs = DigitalInOut(board.D9)
# esp32_ready = DigitalInOut(board.D10)
# esp32_reset = DigitalInOut(board.D5)

spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

print("Connecting to AP...")
while not esp.is_connected:
    try:
        esp.connect_AP(secrets["ssid"], secrets["password"])
    except RuntimeError as e:
        print("could not connect to AP, retrying: ", e)
        continue
print("Connected to", str(esp.ssid, "utf-8"), "\tRSSI:", esp.rssi)

# Initialize a requests object with a socket and esp32spi interface
socket.set_interface(esp)
requests.set_socket(socket, esp)

# DisplayIO Setup
# Set up fonts
font_small = bitmap_font.load_font("/fonts/Arial-12.bdf")
font_large = bitmap_font.load_font("/fonts/Arial-14.bdf")
# preload fonts
glyphs = b'0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-,.: '
font_small.load_glyphs(glyphs)
font_large.load_glyphs(glyphs)

group_verification = displayio.Group(max_size=25)
label_overview_text = Label(font_large,
                        x=0,
                        y=45,
                        text="To authorize this device with Google:")
group_verification.append(label_overview_text)

label_verification_url = Label(font_small,
                               x=0,
                               y=100,
                               line_spacing=1,
                               max_glyphs=90)
group_verification.append(label_verification_url)

label_user_code = Label(font_small,
                        x=0,
                        y=150,
                        max_glyphs=50)
group_verification.append(label_user_code)

label_qr_code = Label(font_small,
                        x=0,
                        y=190,
                        text="Or scan the QR code:")
group_verification.append(label_qr_code)

### helper methods ###
def bitmap_QR(matrix):
    # monochome (2 color) palette
    BORDER_PIXELS = 2

    # bitmap the size of the screen, monochrome (2 colors)
    bitmap = displayio.Bitmap(
        matrix.width + 2 * BORDER_PIXELS, matrix.height + 2 * BORDER_PIXELS, 2
    )
    # raster the QR code
    for y in range(matrix.height):  # each scanline in the height
        for x in range(matrix.width):
            if matrix[x, y]:
                bitmap[x + BORDER_PIXELS, y + BORDER_PIXELS] = 1
            else:
                bitmap[x + BORDER_PIXELS, y + BORDER_PIXELS] = 0
    return bitmap


# The following methods are used for obtaining OAuth 2.0 access tokens
# https://developers.google.com/identity/protocols/oauth2/limited-input-device
def poll_google_auth_server(interval_time, expiration_time):
    """Blocking method which polls Google's authorization server endpoint.
        Returns an access token and refresh token if successful.
    :param int interval_time: Time to wait between requests, in seconds.
    :param int expiration_time: Length of time that the device code is valid, in seconds.

    """
    # construct request parameters
    headers_auth_endpoint = {"Content-Type": "application/x-www-form-urlencoded",
                             "Content-Length":"0"}
    url_auth_endpoint = "https://oauth2.googleapis.com/token?client_id={0}" \
                         "&client_secret={1}&device_code={2}" \
                         "&grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Adevice_code".format(
                         secrets['google_auth_cid'], secrets['google_auth_secret'], device_code)
    # blocking polling loop to POST to endpoint and wait for response
    start_time = time.monotonic()
    while True:
        if not time.monotonic() - start_time < expiration_time:
            print("Code expired, fetching a new code...")
            # fetch a new code
            resp = request_device_user_codes()
            # update the display with the new code
            display_user_code(resp['user_code'], resp['verification_url'])
            # reset timer
            start_time = time.monotonic()
        resp = requests.post(url_auth_endpoint, headers=headers_auth_endpoint)
        resp_json = resp.json()
        if "access_token" in resp_json:
            print("Access granted!")
            break
        # sleep for interval_time specified by oauth
        time.sleep(interval_time)
    return resp_json["access_token"], resp_json["refresh_token"]

def request_device_user_codes():
    """Sends a HTTP POST request to Google's authorization server
    that identifies your application and the access scope.

    Returns: json-formatted response
    """
    URL = "https://oauth2.googleapis.com/device/code?client_id={0}&scope=https://www.googleapis.com/auth/calendar.readonly".format(secrets['google_auth_cid'])
    HEADERS = {"Host": "oauth2.googleapis.com",
               "Content-Type": "application/x-www-form-urlencoded",
               "Content-Length":"0"}
    response = requests.post(URL, headers=HEADERS)
    return response.json()

print("Requesting device and user codes...")
resp = request_device_user_codes()
# unique device identifier
device_code = resp['device_code']
# length of time, in seconds that the codes above are valid
expiration_time = resp['expires_in']
# length of time we'll wait between polling the auth. server
polling_time = resp['interval']
# url user must navigate to on a browser
verification_url = resp['verification_url']
# identifies scopes requested by the application
user_code = resp['user_code']

# Display user code and verification URL
print("To authorize this device with Google: ")
print("1)On your computer, go to: %s"%verification_url)
print("2)Enter code: %s"%user_code)

# modify display labels to show verification URL and user code
label_verification_url.text = "1. On your computer or mobile device,\n    go to: %s"%verification_url
label_user_code.text = "2. Enter code: %s"%user_code

# Create a QR code
qr = adafruit_miniqr.QRCode(qr_type=3, error_correct=adafruit_miniqr.L)
qr.add_data(verification_url.encode())
qr.make()

# generate the 1-pixel-per-bit bitmap
qr_bitmap = bitmap_QR(qr.matrix)
# we'll draw with a classic black/white palette
palette = displayio.Palette(2)
palette[0] = 0xFFFFFF
palette[1] = 0x000000
# we'll scale the QR code as big as the display can handle
scale = 15
# then center it!
qr_img = displayio.TileGrid(qr_bitmap,
                            pixel_shader=palette,
                            x=170, y=165)
group_verification.append(qr_img)
# show the group
board.DISPLAY.show(group_verification)


print("Polling google's auth server...")
access_token, refresh_token = poll_google_auth_server(polling_time, expiration_time)
# Store in Non-volatile memory


# print formatted keys for adding to secrets.py
print("Successfully Authenticated!\nAdd the following lines to your secrets.py file:")
print('\t\'google_auth_access_token\' ' + ":" + " \'%s\',"%access_token)
print('\t\'google_auth_refresh_token\' ' + ":" + " \'%s\'"%refresh_token)
# TODO: Check for SD Card
# Remove QR code and code/verification labels
group_verification.pop()
group_verification.pop()

label_overview_text.text = "You are authorized!"
label_verification_url.text = "Please check the REPL for codes to add to your secrets.py file"

# prevent exit
while True:
    pass