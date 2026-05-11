#include <avr/io.h>


.global main
main:
    ldi r16, 0xFF
    out _SFR_IO_ADDR(DDRB), r16

loop:
    out _SFR_IO_ADDR(PORTB), r16
    rjmp loop
