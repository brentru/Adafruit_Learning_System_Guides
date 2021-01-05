# PyPortal Google Calendar Viewer
# Brent Rubell for Adafruit Industries, 2021
import time
import board
import busio
from digitalio import DigitalInOut
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from adafruit_esp32spi import adafruit_esp32spi
import adafruit_requests as requests
import sdcardio
import storage

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

# Set access and refresh tokens locally so we can refresh them
access_token = secrets['google_auth_access_token']
refresh_token = secrets['google_auth_refresh_token']

def refresh_access_token():
    """Returns a new access token.
    https://developers.google.com/identity/protocols/oauth2/limited-input-device#offline

    """
    URL = "https://oauth2.googleapis.com/token&client_id={0}&client_secret={1}&refresh_token={2}&grant_type=refresh_token".format(secrets['google_auth_cid'], secrets['google_auth_secret'], refresh_token)
    HEADERS = {"Host": "oauth2.googleapis.com",
               "Content-Type": "application/x-www-form-urlencoded",
               "Content-Length":"0"}
    response = requests.post(URL, headers=HEADERS)
    print(response.text)
    resp_json = response.json()
    print(resp_json)
    #return resp_json['access_token']

def get_calendar_events(calendar_id, max_events):
    """Returns events on a specified calendar.

    """
    URL = "https://www.googleapis.com/calendar/v3/calendars/{0}" \
          "/events?maxResults={1}&singleEvents=true".format(calendar_id, max_events)
    HEADERS = {'Authorization': 'Bearer ' + access_token,
               'Accept': 'application/json',
               "Content-Length":"0"}
    response = requests.get(URL, headers=HEADERS)
    print(response.json())

#access_token = refresh_access_token()
print("obtaining calendar events..")
get_calendar_events(CALENDAR_ID, MAX_EVENTS)