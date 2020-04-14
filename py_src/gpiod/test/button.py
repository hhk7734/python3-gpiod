import gpiod
import sys
from datetime import timedelta

try:
    if len(sys.argv) > 2:
        BUTTON_CHIP = sys.argv[1]
        BUTTON_LINE_OFFSET = int(sys.argv[2])
        if len(sys.argv) > 3:
            edge = sys.argv[3]
            if edge[0] == 'r':
                BUTTON_EDGE = gpiod.line_request.EVENT_RISING_EDGE
            elif edge[0] == 'f':
                BUTTON_EDGE = gpiod.line_request.EVENT_FALLING_EDGE
            else:
                BUTTON_EDGE = gpiod.line_request.EVENT_BOTH_EDGES
        else:
            BUTTON_EDGE = gpiod.line_request.EVENT_BOTH_EDGES

    else:
        raise Exception()
except:
    print('''Usage:
    python3 -m gpiod.test.button <chip> <line offset> [rising|falling|both]''')
    sys.exit()

chip = gpiod.chip(BUTTON_CHIP)
button = chip.get_line(BUTTON_LINE_OFFSET)

config = gpiod.line_request()
config.consumer = "Button"
config.request_type = BUTTON_EDGE

button.request(config)

print("event fd: ", button.event_get_fd())

while True:
    if button.event_wait(timedelta(seconds=10)):
        # event_read() is blocking function.
        event = button.event_read()
        if event.event_type == gpiod.line_event.RISING_EDGE:
            print("rising: ", event.timestamp)
        else:
            print("falling: ", event.timestamp)
    else:
        print("timeout(10s)")
