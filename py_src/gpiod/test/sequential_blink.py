import gpiod
import sys
import time

try:
    if len(sys.argv) > 2:
        LED_CHIP = sys.argv[1]
        LED_LINE_OFFSETS = []
        for i in range(len(sys.argv) - 2):
            LED_LINE_OFFSETS.append(int(sys.argv[i+2]))
    else:
        raise Exception()
except:
    print('''Usage:
    python3 -m gpiod.test.sequential_blink <chip> <line offset1> \\
        [<line offset2> ...]''')
    sys.exit()

chip = gpiod.chip(LED_CHIP)
leds = chip.get_lines(LED_LINE_OFFSETS)

config = gpiod.line_request()
config.request_type = gpiod.line_request.DIRECTION_OUTPUT

for i in range(leds.size):
    config.consumer = "Blink{}".format(i)
    leds.get(i).request(config)
    print("line: ", leds[i].offset, ", consumer: ", leds[i].consumer)

while True:
    for led in leds:
        led.set_value(1)
        time.sleep(0.2)
        led.set_value(0)
