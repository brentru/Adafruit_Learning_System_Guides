# PyPortal Google Calendar Viewer
# Brent Rubell for Adafruit Industries, 2021
import time
import board
import busio
from digitalio import DigitalInOut
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from adafruit_esp32spi import adafruit_esp32spi
import adafruit_requests as requests
from adafruit_oauth2 import OAuth2

# Calendar ID
CALENDAR_ID = "ajfon6phl7n1dmpjsdlevtqa04@group.calendar.google.com"

# Maximum amount of events to display
MAX_EVENTS = 3

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

# Initialize an OAuth2 object
scopes = ["https://www.googleapis.com/auth/calendar.readonly"]
google_auth = OAuth2(
    requests, secrets["google_client_id"],
    secrets["google_client_secret"], scopes,
    secrets["google_access_token"],
    secrets["google_refresh_token"]
)

# Initial refresh of access token
print("Refreshing access token..")
google_auth.refresh_access_token()
# TODO: Take a timestamp of when we requested this
# so we can check against expiration!
if not google_auth.refresh_access_token():
    raise RuntimeError("Unable to refresh access token - has the token been revoked?")

def get_calendar_events(calendar_id, max_events):
    """Returns events on a specified calendar.

    """
    header = {'Accept': 'application/json',
              "Content-Length": "0"}
    url = "https://www.googleapis.com/calendar/v3/calendars/{0}" \
          "/events?maxResults={1}&singleEvents=true" \
          "&key={2}".format(calendar_id, max_events, google_auth.access_token)
    response = requests.post(url, headers=header)
    return response.json()

print("obtaining calendar events..")
resp = get_calendar_events(CALENDAR_ID, MAX_EVENTS)
print(resp)