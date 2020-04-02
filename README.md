![license](https://img.shields.io/github/license/hhk7734/python3-gpiod)
![pypi](https://img.shields.io/pypi/v/gpiod)
![language](https://img.shields.io/github/languages/top/hhk7734/python3-gpiod)

# python3-gpiod

Ref: <a href="https://git.kernel.org/pub/scm/libs/libgpiod/libgpiod.git" target=_blank>https://git.kernel.org/pub/scm/libs/libgpiod/libgpiod.git</a>

## Installation

```shell
sudo apt update \
&& sudo apt install -y python3 python3-dev python3-pip pkg-config \
    gpiod libgpiod-dev
```

```shell
python3 -m pip install -U --user pip gpiod
```

If you see **"OSError: pkg-config: Failed to find libgpiodcxx."**, you need to install libgpiodcxx manually.

```shell
sudo apt purge -y gpiod libgpiod-dev
```

```shell
sudo apt install -y git libtool autoconf-archive
```

```shell
git clone git://git.kernel.org/pub/scm/libs/libgpiod/libgpiod.git \
&& cd libgpiod
```

If the kernel version is 5.4 or lower, use **`git checkout v1.4.2`** to change the version.(Change it to v1.1 or more and less than v1.5)

```shell
./autogen.sh --enable-tools=yes --prefix=/usr --enable-bindings-cxx \
&& make \
&& sudo make install
```

```shell
python3 -m pip install -U --user gpiod
```

## help command

```python
>>> import gpiod
>>> help(gpiod)
>>> help(gpiod.chip)
>>> help(gpiod.chip.get_line)

Help on instancemethod in module gpiod._gpiod:

get_line(...)
    get_line(self: gpiod._gpiod.chip, offset: int) -> gpiod::line

    /**
     * @brief Get the line exposed by this chip at given offset.
     * @param offset Offset of the line.
     * @return Line object.
     */
```

## Test

```shell
python3 -m gpiod.test.blink <chip> <line offset>
python3 -m gpiod.test.blinks <chip> <line offset1> [<line offset2> ...]
python3 -m gpiod.test.sequential_blink <chip> <line offset1> \
    [<line offset2> ...]
python3 -m gpiod.test.button <chip> <line offset> [rising|falling|both]
```

## Blink example

### Python3

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

### C++

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
