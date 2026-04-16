#include <avr/io.h>
#include <util/delay.h>
#include <stdbool.h>
#include <avr/interrupt.h>
#include <avr/sleep.h>
#include <avr/wdt.h>
#include <avr/eeprom.h>

#include "bdm.h"

/* 
 * PIN MAPPINGS (Corrected for Binary Alignment)
 * ----------------------------------
 * RTC4543SB:
 *   CLK:  PB5, DATA: PC4, CE: PB1, WR: PB3
 *
 * TARGET (BDM Device):
 *   DSCLK: PC0, DSI: PC3, DSO: PD6
 *
 * INTRUSION:
 *   PROBE: PB1 (Pulsed), SENSE: PD5 (T1 Input)
 */

#define LED_PIN         PD1
#define PHOTO_PIN       ADC1  // Photodiode on ADC1 (PC1)

#define BDM_DSCLK_PIN   PC0
#define BDM_DSI_PIN     PC3
#define BDM_DSO_PIN     PD6
#define BDM_DSO_IN      PIND
#define BDM_FREEZE_PIN  PB2

#define RTC_CLK_PIN     PB5
#define RTC_DATA_PIN    PC4
#define RTC_CE_PIN      PB1
#define RTC_WR_PIN      PB3

// MC68332 Register Addresses
#define SIMCR               0x00FFFA00
#define SYNCR               0x00FFFA04
#define SYPCR               0x00FFFA20
#define CSPAR0              0x00FFFA44
#define CSPAR1              0x00FFFA46
#define CSBARBT             0x00FFFA48
#define CSORBT              0x00FFFA4A
#define CSBAR0              0x00FFFA4C
#define CSOR0               0x00FFFA4E

volatile uint8_t g_state = 0x01;

uint16_t bdm_transfer(uint16_t data_out) {
    uint32_t val = (uint32_t)data_out;
    for (uint8_t i = 0; i < 15; i++) val <<= 1;
    
    for (uint8_t i = 0; i < 17; i++) {
        bool bit = (val & 0x10000);
        val <<= 1;
        
        PORTC &= ~((1 << BDM_DSCLK_PIN) | (1 << BDM_DSI_PIN));
        _delay_us(2); // 5-loop delay
        
        if (bit) PORTC |= (1 << BDM_DSI_PIN);
        if (PIND & (1 << BDM_DSO_PIN)) val |= 1;
        
        PORTC |= (1 << BDM_DSCLK_PIN);
        _delay_us(2);
    }
    return (uint16_t)(val & 0xFFFF);
}

void bdm_write_word(uint32_t addr, uint16_t data) {
    bdm_transfer(BDM_WRITE | SIZE_WORD); // WRITE(B/W)
    bdm_transfer(addr >> 16); // MS ADDR
    bdm_transfer(addr & 0xFFFF); // LS ADDR
    bdm_transfer(data); // DATA
    // WRITE MEMORY LOCATION
}

typedef struct {
    uint8_t sec, min, hour, day, month, year, week;
} rtc_time_t;

void rtc_read_52bits(uint8_t *buffer) {
    for (uint8_t i = 0; i < 7; i++) buffer[i] = 0;
    PORTB &= ~(1 << RTC_WR_PIN);
    PORTB |= (1 << RTC_CE_PIN);
    _delay_us(2);
    for (uint8_t i = 0; i < 52; i++) {
        PORTB |= (1 << RTC_CLK_PIN);
        _delay_us(2);
        if (PINC & (1 << RTC_DATA_PIN)) {
            buffer[i/8] |= (1 << (i%8));
        }
        PORTB &= ~(1 << RTC_CLK_PIN);
        _delay_us(2);
    }
    PORTB &= ~(1 << RTC_CE_PIN);
}

uint8_t check_intrusion() {
    TCCR1A = 0;
    TCCR1B = 0;
    TCNT1 = 0;
    PINB = (1 << PB1); // Toggle PB1 probe
    TCCR1B = 0x07;     // Ext clock on T1 (PD5), rising edge
    
    // Software delay
    for (volatile uint16_t i = 7999; i > 0; i--);
    
    TCCR1B = 0; // Stop timer
    return (TCNT1 >= 0x15); 
}

void target_init() {
    bdm_write_word(SIMCR,   0x40CF);
    bdm_write_word(SYNCR,   0x7F03);
    _delay_ms(20);
    bdm_write_word(SYPCR,   0x004C);
    bdm_write_word(CSPAR0,  0x3FFF);
    bdm_write_word(CSPAR1,  0x03FD);
    bdm_write_word(CSBARBT, 0x0007);
    bdm_write_word(CSORBT,  0x6C70);
    bdm_write_word(CSBAR0,  0x0007);
    bdm_write_word(CSOR0,   0x7470);
    
    for (uint16_t addr = 0; addr < 0x40; addr += 2) {
        uint16_t data = eeprom_read_word((uint16_t*)addr);
        bdm_write_word(0x3C0 + addr, data);
    }
}

void system_init() {
    cli();
    // Watchdog Disable
    wdt_reset();
    WDTCSR |= (1 << WDCE) | (1 << WDE);
    WDTCSR = 0x00;
    
    // Power Reduction and Digital Input Disable
    PRR = 0xAE; 
    DIDR0 = 0x2E;
    DIDR1 = 0x02;
    
    // Pin Directions
    DDRB |= (1 << PB1) | (1 << PB3) | (1 << PB5);
    DDRC |= (1 << PC0) | (1 << PC3);
    DDRC &= ~(1 << PC4);
    DDRD &= ~((1 << PD4) | (1 << PD5) | (1 << PD6));
    
    PORTC |= (1 << PC0) | (1 << PC3);
    
    // Timer 1 Setup
    TCCR1A = 0x00;
    TCCR1B = 0x04; // Initial prescaler
    TCCR1C = 0x00;
    
    sei();
}

int main() {
    system_init();
    
    uint8_t buf[7];
    rtc_read_52bits(buf);
    rtc_read_52bits(buf); // Double read
    
    while (1) {
        switch (g_state) {
            case 0x01: // Idle
                if (check_intrusion()) {
                    g_state = 0x02; // Intrusion detected
                } else {
                    set_sleep_mode(SLEEP_MODE_PWR_DOWN);
                    TCCR0B = (TCCR0B & 0xF1) | 0x04;
                    TCCR0B |= 0x01;
                    sleep_mode();
                    TCCR0B &= ~0x01;
                }
                break;
            case 0x02: // Intrusion
                target_init();
                g_state = 0x03;
                break;
            case 0x03: // Active
                if (!check_intrusion()) {
                    g_state = 0x01;
                }
                // Long delay
                for (volatile uint32_t i = 0x1869ff; i > 0; i--);
                break;
        }
    }
}
