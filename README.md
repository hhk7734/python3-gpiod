![license](https://img.shields.io/github/license/hhk7734/python3-gpiod)
![pypi](https://img.shields.io/pypi/v/gpiod)
![language](https://img.shields.io/github/languages/top/hhk7734/python3-gpiod)

# python3-gpiod

## Installation

```shell
sudo apt update \
&& sudo apt install -y python3 python3-dev python3-pip \
    gpiod libgpiod-dev pkg-config
```

```shell
python3 -m pip install -U --user pip gpiod
```

## Blink example

```python
import gpiod
import sys
import time

try:
    if len(sys.argv) > 2:
        LED_CHIP = sys.argv[1]
        LED_LINE_OFFSET = int(sys.argv[2])
    else:
        raise
except:
    print('''Usage:
    python3 blink.py <chip> <line offset>''')
    sys.exit()

chip = gpiod.chip(LED_CHIP)

print(f"chip name: {chip.name()}")
print(f"chip label: {chip.label()}")
print(f"number of lines: {chip.num_lines()}")

led = chip.get_line(LED_LINE_OFFSET)

config = gpiod.line_request()
config.consumer = "Blink"
config.request_type = gpiod.line_request.DIRECTION_OUTPUT

led.request(config)

print(f"line offset: {led.offset()}")
print(f"line name: {led.name()}")
print(f"line consumer: {led.consumer()}")
print("line direction: " + ("input" if (led.direction()
                                        == gpiod.line.DIRECTION_INPUT) else "output"))
print("line active state: " + ("active low" if (led.active_state()
                                                == gpiod.line.ACTIVE_LOW) else "active high"))

while True:
    led.set_value(0)
    time.sleep(0.3)
    led.set_value(1)
    time.sleep(0.3)
```

## Changelog

Ref: CHANGELOG
