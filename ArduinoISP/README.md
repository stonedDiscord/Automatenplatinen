# ArduinoISP

A PCB to use an Arduino Nano as an In-Circuit Serial Programmer (ISP) for programming AVR microcontrollers.

![ArduinoISP PCB](arduinoisp.png)

## Overview

This board allows an Arduino Nano to function as an ISP programmer, enabling you to burn bootloaders to other Arduinos and program AVR chips like the ATmega series, or ATtiny microcontrollers.

### What is Arduino as ISP?

Arduino ISP turns your Arduino into an in-circuit programmer to re-program AVR chips. The bootloader is a small piece of code (usually 512 bytes) that executes at every reset and allows sketches to be uploaded via serial/USB. To program the bootloader and configure fuses properly, you need an ISP programmer that connects to the microcontroller's SPI pins (MOSI, MISO, SCK) and reset pin.

## Hardware

The PCB includes:

- **Two 15-pin headers** for connecting to an Arduino Nano:
  - **J1 (Analog)**: Pins for A0-A7, AREF, 3V3, and power
  - **J2 (Digital)**: Pins for D0-D13, GND, and power
- **AVR-ISP-6 connector (J4)**: Standard 6-pin ISP programming header for target devices
- **Status LED (D3)**: Visual feedback during programming
- **Pull-up resistors (R2, R3)**: 220Ω current limiting for LEDs
- **Mounting holes**: For securing the board

### Pin Mapping

The ISP programming uses the following connections from the Nano to the 6-pin ISP connector:

| ISP Pin | Signal | Nano Pin |
|---------|--------|----------|
| 1 | MISO | D12 |
| 2 | VCC | +5V |
| 3 | SCK | D13 |
| 4 | MOSI | D11 |
| 5 | RST | D10 |
| 6 | GND | GND |

## Usage

### 1. Program the Arduino Nano

1. Open the ArduinoISP sketch: `File > Examples > 11.ArduinoISP > ArduinoISP`
2. Select your Nano board and port
3. Upload the sketch to the Nano

You can also find the sketch on the [official Arduino GitHub page](https://github.com/arduino/arduino-examples/blob/main/examples/11.ArduinoISP/ArduinoISP/ArduinoISP.ino)

### 2. Wire the Boards

Connect the Nano to this PCB's headers. The board will provide the 6-pin ISP connector for connecting to your target device.

### 3. Burn the Bootloader

1. Select the target board type in `Tools > Board`
2. Select `Arduino as ISP` in `Tools > Programmer`
3. Use `Tools > Burn Bootloader`

## Requirements

- Arduino Nano
- Target AVR microcontroller board
- Arduino IDE

## Notes

- Be cautious when programming 3.3V devices (Due, Zero, etc.) - ensure the jumper is set correctly.