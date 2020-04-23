# pylint: disable=missing-docstring
import sys
from datetime import timedelta
from .. import chip, line_request, line_event

try:
    if len(sys.argv) > 3:
        BUTTON_CHIP = sys.argv[1]
        BUTTON_LINE_OFFSETS = []
        for i in range(len(sys.argv) - 3):
            BUTTON_LINE_OFFSETS.append(int(sys.argv[i + 2]))

        edge = sys.argv[len(sys.argv) - 1]
        if edge[0] == "r":
            BUTTON_EDGE = line_request.EVENT_RISING_EDGE
        elif edge[0] == "f":
            BUTTON_EDGE = line_request.EVENT_FALLING_EDGE
        else:
            BUTTON_EDGE = line_request.EVENT_BOTH_EDGES
    else:
        raise Exception()
# pylint: disable=broad-except
except Exception:
    print(
        """Usage:
    python3 -m test.bulk_button <chip> <line offset> [<line offset2> ...]
        <[rising|falling|both]>"""
    )
    sys.exit()

c = chip(BUTTON_CHIP)
buttons = c.get_lines(BUTTON_LINE_OFFSETS)

config = line_request()
config.request_type = BUTTON_EDGE

for i in range(buttons.size):
    config.consumer = "Button {}".format(i)
    buttons[i].request(config)


while True:
    lines = buttons.event_wait(timedelta(seconds=10))
    if not lines.empty:
        for it in lines:
            event = it.event_read()
            print(it.consumer, " ", end="")
            if event.event_type == line_event.RISING_EDGE:
                print("rising: ", end="")
            else:
                print("falling: ", end="")
            print(event.timestamp)
    else:
        print("timeout(10s)")
