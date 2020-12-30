# adafruit_requests usage with an esp32spi_socket
import board
import busio
from digitalio import DigitalInOut
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from adafruit_esp32spi import adafruit_esp32spi
import adafruit_requests as requests

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

### helper methods ###
def display_user_code(user_code, verification_url):
    """Displays the verificaiton URL and user code to the user.
    "param str user_code: identifies scopes requested by the application
    :param str verification_url: url user must navigate to on a browser.
    """
    # display the user code
    # NOTE: user_code must be displayed with a length field of 15 wide

    # display the verification url
    # NOTE: Length must be 40 characters long
    pass

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



# Request device and user codes
print("POSTing data")
URL = "https://oauth2.googleapis.com/device/code?client_id={0}&scope=https://www.googleapis.com/auth/calendar.readonly".format(secrets['google_client_id'])
HEADERS = {"Host": "oauth2.googleapis.com",
                     "Content-Type": "application/x-www-form-urlencoded",
                     "Content-Length":"0"}
response = requests.post(URL, headers=HEADERS)
print("-" * 40)

# TODO: add some handling, if we cant parse or response back is invalid
json_resp = response.json()
print(json_resp)

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

display_user_code()