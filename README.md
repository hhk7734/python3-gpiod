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

if len(sys.argv) > 2:
    LED_CHIP = sys.argv[1]
    LED_LINE_OFFSET = int(sys.argv[2])
else:
    print('''Usage:
    python3 blink.py <chip> <line offset>''')
    sys.exit()

chip = gpiod.chip(LED_CHIP)
led = chip.get_line(LED_LINE_OFFSET)

config = gpiod.line_request()
config.consumer = "Blink"
config.request_type = gpiod.line_request.DIRECTION_OUTPUT

led.request(config)

while True:
    led.set_value(0)
    time.sleep(0.1)
    led.set_value(1)
    time.sleep(0.1)
```

```c++
#include <chrono>
#include <cstdlib>
#include <gpiod.hpp>
#include <iostream>
#include <string>
#include <thread>

int main(int argc, char **argv) {
    std::string LED_CHIP;
    int         LED_LINE_OFFSET;

    if(argc > 2) {
        LED_CHIP        = argv[1];
        LED_LINE_OFFSET = std::stoi(argv[2]);
    } else {
        std::cout << "Usage:" << std::endl
                  << "    ./blink <chip> <line offset>" << std::endl;
        std::exit(0);
    }

    gpiod::chip chip(LED_CHIP);
    gpiod::line led = chip.get_line(LED_LINE_OFFSET);

    gpiod::line_request config;
    config.consumer     = "Blink";
    config.request_type = gpiod::line_request::DIRECTION_OUTPUT;

    led.request(config);

    while(1) {
        led.set_value(0);
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        led.set_value(1);
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }
}
```

```shell
g++ -o blink test.cpp -lgpiodcxx
```

## Changelog

Ref: CHANGELOG
