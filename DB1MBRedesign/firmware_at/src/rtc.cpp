#include <avr/io.h>
#include <util/delay.h>
#include <avr/sleep.h>
#include <stdint.h>

#include "rtc.h"

// ============================================================================
// RTC support
// ============================================================================

void rtc_4543_read(uint8_t *buffer) {
    for (uint8_t i = 0; i < 7; i++) buffer[i] = 0;
    
    // WR high (read mode), CE high to start transfer
    PORTB |= (1 << RTC_WR_PIN) | (1 << RTC_CE_PIN);
    _delay_us(1);
    
    // Clock out 52 bits, sample DATA on each rising edge
    for (uint8_t bit = 0; bit < 52; bit++) {
        PORTB |= (1 << RTC_CLK_PIN);
        _delay_us(1);
        if (PINC & (1 << RTC_DATA_PIN)) {
            buffer[bit / 8] |= (1 << (bit % 8));
        }
        PORTB &= ~(1 << RTC_CLK_PIN);
        _delay_us(1);
    }
    
    // CE low to latch
    PORTB &= ~(1 << RTC_CE_PIN);
}
