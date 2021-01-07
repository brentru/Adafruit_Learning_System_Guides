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
import displayio
from adafruit_display_shapes.line import Line
from adafruit_pyportal import PyPortal
import rtc

# Calendar ID
CALENDAR_ID = "ajfon6phl7n1dmpjsdlevtqa04@group.calendar.google.com"

# Maximum amount of events to display
MAX_EVENTS = 3

# Amount of time to wait between refreshing the calendar, in minutes
REFRESH_TIME = 15

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

# Create the PyPortal object
pyportal = PyPortal(esp=esp, external_spi=spi)
r = rtc.RTC()

# Initialize a requests object with a socket and esp32spi interface
socket.set_interface(esp)
requests.set_socket(socket, esp)

# Initialize an OAuth2 object with GCal API scope
scopes = ["https://www.googleapis.com/auth/calendar.readonly"]
google_auth = OAuth2(
    requests, secrets["google_client_id"],
    secrets["google_client_secret"], scopes,
    secrets["google_access_token"],
    secrets["google_refresh_token"]
)

# Initial refresh of access token
print("Refreshing access token..")
# TODO: Take a timestamp of when we requested this
# so we can check against expiration!
if not google_auth.refresh_access_token():
    raise RuntimeError("Unable to refresh access token - has the token been revoked?")
# TODO: Removeee
print(google_auth.access_token)

# DisplayIO
frame = displayio.Group(max_size=15)

# Add a white background
background = displayio.Group(max_size=1)
color_bitmap = displayio.Bitmap(
    board.DISPLAY.width, board.DISPLAY.height, 1
)
color_palette = displayio.Palette(1)
color_palette[0] = 0xFFFFFF
bg_sprite = displayio.TileGrid(
        color_bitmap,
        pixel_shader=color_palette,
        x=0, y=0)
background.append(bg_sprite)
frame.append(background)

# Add the header
line_header = Line(0, 60, 320, 60, color=0x000000)
frame.append(line_header)
# TODO: Add font to header

board.DISPLAY.show(frame)

def get_current_time():
    """Gets local time from Adafruit IO and converts to RFC3339 timestamp.

    """
    # Get local time from Adafruit IO
    pyportal.get_local_time(secrets['timezone'])
    # Format as RFC339 timestamp
    cur_time = r.datetime
    cur_time = '{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}{:s}'.format(cur_time[0],
    cur_time[1], cur_time[2], cur_time[3], cur_time[4], cur_time[5], "Z")
    return cur_time

def get_calendar_events(calendar_id, max_events, time_min):
    """Returns events on a specified calendar.
    Response is a list of events ordered by their start date/time in ascending order.
    """
    headers = {'Authorization': 'Bearer ' + google_auth.access_token,
               'Accept': 'application/json',
               "Content-Length":"0"}
    url = "https://www.googleapis.com/calendar/v3/calendars/{0}" \
    "/events?maxResults={1}&timeMin={2}&orderBy=startTime" \
    "&singleEvents=true".format(calendar_id, max_events, time_min)
    resp = requests.get(url, headers=headers)
    resp_json = resp.json()
    if 'error' in resp_json:
        raise RuntimeError("Error:", resp_json)
    resp.close()
    # parse the 'items' array so we can iterate over it easier
    events = []
    event_items = resp_json['items']
    for event in range(0, max_events):
        events.append(event_items[event])
    return events

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

def display_calendar_events(events):
    # Display all calendar events
    for event_idx in range(len(MAX_EVENTS)):
        event = events[event_idx]
        event_name = event['summary']
        event_start = event['start']['dateTime']
        event_end = event['end']['dateTime']
        print("Event name: ", event_name)
        # TODO: Parse the times 
        print('Event start:' , event_end)
        print('Event ends:', event_end)
        print("---")
        # TODO
        # Generate new row to hold event details
        #line_event_row = Line(0, 60*(idx_event+2), 320, 60*(idx_event+2), color=0x000000)
        #frame.append(line_event_row)
        # Generate new label to hold event info
        # TODO



while True:
    # fetch calendar events!
    print("fetching local time...")
    now = get_current_time()
    print("fetching calendar events...")
    events = get_calendar_events(CALENDAR_ID, MAX_EVENTS, now)
    display_calendar_events(events)

    # sleep for REFRESH_TIME minutes before fetching data again
    time.sleep(REFRESH_TIME * 60)
