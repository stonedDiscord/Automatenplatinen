/**
 * Copyright (C) PlatformIO <contact@platformio.org>
 * See LICENSE for details.
 */

#include <avr/io.h>
#include <util/delay.h>

int main(void)
{
  SREG = 0;

  // make the LED pin an output for PORTD1
  DDRD = 1 << 1;

  while (1)
  {
    _delay_ms(500);

    // toggle the LED
    PORTD ^= 1 << 1;
  }

  return 0;
}