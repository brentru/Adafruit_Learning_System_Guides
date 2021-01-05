# PyPortal Google Calendar Viewer
# Brent Rubell for Adafruit Industries, 2021
import time
import board
import busio
from digitalio import DigitalInOut
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from adafruit_esp32spi import adafruit_esp32spi
import adafruit_requests as requests

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
    URL = "https://oauth2.googleapis.com/token?" \
          "client_id={0}" \
          "&client_secret={1}&grant_type=refresh_token" \
          "&refresh_token={2}".format(secrets['google_auth_cid'], \
          secrets['google_auth_secret'], secrets['google_auth_refresh_token'])
    HEADERS = {"Host": "oauth2.googleapis.com",
               "Content-Type": "application/x-www-form-urlencoded",
               "Content-Length":"0"}
    response = requests.post(URL, headers=HEADERS)
    resp_json = response.json()
    return resp_json['access_token']

def get_calendar_events(calendar_id, max_events, time_min=None):
    """Returns events on a specified calendar.
    Response is events ordered by their start date/time in ascending order.

    """
    if time_min:
        URL = "https://www.googleapis.com/calendar/v3/calendars/{0}" \
        "/events?maxResults={1}&timeMin={2}&orderBy=startTime&singleEvents=true".format(calendar_id, max_events, time_min)
    else:
        URL = "https://www.googleapis.com/calendar/v3/calendars/{0}" \
            "/events?maxResults={1}&orderBy=startTime&singleEvents=true".format(calendar_id, max_events)
    HEADERS = {'Authorization': 'Bearer ' + access_token,
               'Accept': 'application/json',
               "Content-Length":"0"}
    response = requests.get(URL, headers=HEADERS)
    return response.json()

def format_time(timestamp, current_time):
    """Formats an ISO-8601 timestamped time from Google Events API, returns a formatted string.

    :param str timestamp: ISO-8601 timestamp.
    """
    times = timestamp.split("T")
    the_date = times[0]
    the_time = times[1]
    year, month, mday = [int(x) for x in the_date.split("-")]
    the_time = the_time.split("-")[0]
    hours, minutes, seconds = [int(x) for x in the_time.split(":")]
    # TODO: The following should be stftime formatted better!
    # check if event is happening today
    curr_date = current_time.split("T")[0]
    curr_date = curr_date.split("-")[2]
    if curr_date == mday:
        return ("{0}:{1}:{2}".format(hours, minutes, seconds))
    # otherwise return the full timestamp
    return ("{0}/{1}/{2} {3}:{4}:{5}".format(mday, month, year, hours, minutes, seconds))

# let's fetch a fresh access token, valid for 60mins
print("refreshing api token...")
access_token = refresh_access_token()
print("obtaining calendar events..")

# prefetch calendar events to obtain an RFC3339 timestamp
resp = get_calendar_events(CALENDAR_ID, 1)
current_time = resp['updated']

# fetch cal events!
resp = get_calendar_events(CALENDAR_ID, MAX_EVENTS, current_time)
# parse out events
calendar_name = resp['summary']
print("Calendar: ", calendar_name)

# scrape datetime from last-updated
calendar_date = resp['updated']

for idx_event in range(MAX_EVENTS):
    # Get calendar events
    event = resp['items'][idx_event]
    event_name = event['summary']
    event_start = event['start']['dateTime']
    event_end = event['end']['dateTime']
    print("Event name: ", event_name)
    print('Event start:' , format_time(event_start, current_time))
    print('Event ends:', format_time(event_end, current_time))
    print("---")

