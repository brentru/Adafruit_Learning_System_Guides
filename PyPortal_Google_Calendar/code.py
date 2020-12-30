# adafruit_requests usage with an esp32spi_socket
import board
import busio
from digitalio import DigitalInOut
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from adafruit_esp32spi import adafruit_esp32spi
import adafruit_requests as requests
# display
import displayio
import terminalio
from adafruit_display_text.label import Label
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

# DisplayIO

# Group for displaying verification code and URL
group_verification = displayio.Group(max_size=25)

# TODO: Center
label_overview_text = Label(terminalio.FONT,
                        x=10,
                        y=0,
                        text="To authorize this device with GCal")
group_verification.append(label_overview_text)

# TODO: Center
label_verification_url = Label(terminalio.FONT,
                               x=0,
                               y=100,
                               max_glyphs=50)
group_verification.append(label_verification_url)

# TODO: Center
label_user_code = Label(terminalio.FONT,
                        x=0,
                        y=150,
                        max_glyphs=30)
group_verification.append(label_user_code)

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

def display_user_code(user_code, verification_url):
    """Displays the verificaiton URL and user code to the user.
    "param str user_code: identifies scopes requested by the application
    :param str verification_url: url user must navigate to on a browser.
    """
    print("To authorize this device with Google")
    print("1)On your computer, go to %s"%verification_url)
    print("2)Enter code: %s"%user_code)
    # create display labels
    label_verification_url.text = "1) Go to: %s"%verification_url
    label_user_code.text = "2) Enter code: %s"%user_code

    # create a QR code
    qr = adafruit_miniqr.QRCode(qr_type=3, error_correct=adafruit_miniqr.L)
    qr.add_data(verification_url.encode())
    qr.make()

    # generate the 1-pixel-per-bit bitmap
    qr_bitmap = bitmap_QR(qr.matrix)
    # We'll draw with a classic black/white palette
    palette = displayio.Palette(2)
    palette[0] = 0xFFFFFF
    palette[1] = 0x000000
    # we'll scale the QR code as big as the display can handle
    scale = min(
        board.DISPLAY.width // qr_bitmap.width, board.DISPLAY.height // qr_bitmap.height
    )
    # then center it!
    pos_x = int(((board.DISPLAY.width / scale) - qr_bitmap.width) / 2)
    pos_y = int(((board.DISPLAY.height / scale) - qr_bitmap.height) / 2)
    qr_img = displayio.TileGrid(qr_bitmap, pixel_shader=palette, x=pos_x, y=pos_y)
    # TODO: Show!
    #group_verification.append(qr_img)
    # show the group
    board.DISPLAY.show(group_verification)

# Poll Google's authorization server
def poll_google_auth_server(interval_time, expiration_time):
    """Blocking method which polls Google's authorization server endpoint.
    :param int interval_time: Time to wait between requests, in seconds.
    :param int expiration_time: Length of time that the device code is valid, in seconds.

    """
    # construct request parameters
    headers_auth_endpoint = {"Content-Type": "application/x-www-form-urlencoded"}
    url_auth_endpoint = "https://oauth2.googleapis.com/token?client_id={0}" \
                         "&client_secret={1}&device_code={3}" \
                         "&grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Adevice_code"
    # blocking polling loop to POST to endpoint and wait for response back
    # NOTE: only poll for length of interval, every interval seconds
    pass

###

# The following steps are used for obtaining OAuth 2.0 access tokens
# https://developers.google.com/identity/protocols/oauth2/limited-input-device
def request_device_user_codes():
    """Sends a HTTP POST request to Google's authorization server
    that identifies your application and the access scope.

    Returns response object.
    """
    URL = "https://oauth2.googleapis.com/device/code?client_id={0}&scope=https://www.googleapis.com/auth/calendar.readonly".format(secrets['google_client_id'])
    HEADERS = {"Host": "oauth2.googleapis.com",
               "Content-Type": "application/x-www-form-urlencoded",
               "Content-Length":"0"}
    # TODO: May need to add some handling code if user provides invalid ID
    response = requests.post(URL, headers=HEADERS)
    return response

### User-Code ###
print("Requesting device and user codes...")
resp = request_device_user_codes()
# Convert to JSON
json_resp = resp.json()
# Parse out what we need from the response...
# unique device identifier
device_code = json_resp['device_code']
# length of time, in seconds that the codes above are valid
expiration_time = json_resp['expires_in']
# length of time we'll wait between polling the auth. server
polling_time = json_resp['interval']
# url user must navigate to on a browser
verification_url = json_resp['verification_url']
# identifies scopes requested by the application
user_code = json_resp['user_code']

print("Displaying user code and verification URL...")
display_user_code(user_code, verification_url)

# TODO
print("Polling google's auth server...")
# poll_google_auth_server(interval_time, expiration_time)

# prevent exit
while True:
    pass