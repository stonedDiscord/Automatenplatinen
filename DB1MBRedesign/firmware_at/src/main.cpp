#include <avr/io.h>
#include <util/delay.h>
#include <stdbool.h>
#include <avr/interrupt.h>
#include <avr/sleep.h>
#include <avr/wdt.h>
#include <avr/eeprom.h>

#include "bdm.h"

/* 
 * PIN MAPPINGS
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



// RTC pins
#define RTC_CLK_PIN     PB5
#define RTC_DATA_PIN    PC4
#define RTC_CE_PIN      PB1
#define RTC_WR_PIN      PB3

// MC68332 ColdFire register addresses (mapped via BDM)
#define SIMCR           0x00FFFA00
#define SYNCR           0x00FFFA04
#define SYPCR           0x00FFFA20
#define CSPAR0          0x00FFFA44
#define CSPAR1          0x00FFFA46
#define CSBARBT         0x00FFFA48
#define CSORBT          0x00FFFA4A
#define CSBAR0          0x00FFFA4C
#define CSOR0           0x00FFFA4E

// System state machine
typedef enum {
    STATE_IDLE      = 0x01,
    STATE_INTRUSION = 0x02,
    STATE_ACTIVE    = 0x03
} system_state_t;

volatile system_state_t g_state = STATE_IDLE;

// ============================================================================
// RTC support
// ============================================================================

void rtc_read_52bits(uint8_t *buffer) {
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

// ============================================================================
// Intrusion detection
// ============================================================================

uint8_t check_intrusion() {
    // Stop and reset Timer1
    TCCR1B = 0;
    TCNT1 = 0;
    
    // Pulse PB1 (probe)
    PORTB |= (1 << PB1);
    _delay_us(10);
    PORTB &= ~(1 << PB1);
    
    // Timer1: external clock on T1 (PD5), rising edge
    TCCR1B = (1 << CS12) | (1 << CS11);  // External clock source
    
    // Software delay while timer counts external pulses on PD5
    for (volatile uint16_t i = 7999; i > 0; i--);
    
    TCCR1B = 0;  // Stop timer
    // Firmware: return 1 if TCNT1 >= 0x15
    return (TCNT1 >= 0x15) ? 1 : 0;
}

// ============================================================================
// Target MC68332 initialization
// ============================================================================

void target_init() {
    // Initialize ColdFire core registers
    bdm_write_word(SIMCR,  0x40CF);
    bdm_write_word(SYNCR,  0x7F03);
    _delay_ms(20);
    bdm_write_word(SYPCR,  0x004C);
    bdm_write_word(CSPAR0, 0x3FFF);
    bdm_write_word(CSPAR1, 0x03FD);
    bdm_write_word(CSBARBT, 0x0007);
    bdm_write_word(CSORBT,  0x6C70);
    bdm_write_word(CSBAR0, 0x0007);
    bdm_write_word(CSOR0,  0x7470);
    
    // Load EEPROM contents to target RAM at 0x3C0 (0x40 words)
    for (uint16_t addr = 0x0000; addr < 0x0040; addr += 2) {
        uint16_t data = eeprom_read_word((uint16_t*)addr);
        bdm_write_word(0x03C0 + addr, data);
    }
    
    // NOTE: Firmware performs additional BDM register writes after EEPROM load
    // (peripheral/timer/UART configuration). TODO
}

// ============================================================================
// Timer2 Compare A ISR – main power‑management / state machine
// ============================================================================

ISR(TIMER2_COMPA_vect) {
    switch (g_state) {
        case STATE_IDLE:
            if (check_intrusion()) {
                g_state = STATE_INTRUSION;
            }
            // Else remain idle – will sleep again
            break;
            
        case STATE_INTRUSION:
            target_init();
            g_state = STATE_ACTIVE;
            break;
            
        case STATE_ACTIVE:
            if (!check_intrusion()) {
                g_state = STATE_IDLE;
            }
            // Long processing delay (~1.6 s) as in firmware
            for (volatile uint32_t i = 1599999; i > 0; i--);
            break;
            
        default:
            g_state = STATE_IDLE;
            break;
    }
}

// ============================================================================
// TIMER0_COMPA ISR – not used; firmware redirects all ints here
// ============================================================================

ISR(TIMER0_COMPA_vect) {
    // Firmware's interrupt vectors for INT0‑7, PCINT, WDT all rjmp to RESET.
    // Empty ISR prevents unwanted resets if accidentally enabled.
}

ISR(TIMER1_COMPA_vect) {
    // Firmware redirects this vector to TIMER0_COMPA. Keep empty.
}

// ============================================================================
// Hardware initialization
// ============================================================================

void system_init() {
    cli();
    
    // Disable watchdog
    wdt_reset();
    WDTCSR |= (1 << WDCE) | (1 << WDE);
    WDTCSR = 0x00;
    
    // Power reduction: turn off unused modules (firmware: PRR=0xAE)
    PRR = 0xAE;
    
    // Digital input disable: disable buffers on ADC/T1 pins
    DIDR0 = 0x2E;
    DIDR1 = 0x02;
    
    // Pin directions (per firmware)
    DDRB |= (1 << PB1) | (1 << PB3) | (1 << PB5);  // RTC CE/WR/CLK outputs
    DDRC |= (1 << PC0) | (1 << PC3);               // BDM DSCLK/DSI outputs
    DDRC &= ~(1 << PC4);                            // RTC DATA input
    DDRD &= ~((1 << PD4) | (1 << PD5) | (1 << PD6)); // Intrusion sense, BDM DSO inputs
    
    // Pull-ups: BDM lines idle high
    PORTC |= (1 << PC0) | (1 << PC3);
    
    // Timer1: stopped; configured in check_intrusion() for ext clock on PD5/T1
    TCCR1A = 0;
    TCCR1B = 0;
    TCCR1C = 0;
    
    // Timer2: async mode, external 32.768 kHz crystal
    // ASSR.AS2=1, TCCR2B:CS22:CS21=11 (ext clock, falling edge), OCR2A=0
    ASSR = (1 << AS2);
    TCCR2A = 0x00;
    TCCR2B = (1 << CS22) | (1 << CS21);
    OCR2A = 0;
    TCNT2 = 0;
    
    // Wait for async registers to synchronize
    while (ASSR & ((1 << TCN2UB) | (1 << OCR2AUB) | (1 << TCR2BUB)));
    
    // Clear Timer2 Compare A flag and enable interrupt
    TIFR2 = (1 << OCF2A);
    TIMSK2 = (1 << OCIE2A);
    
    sei();  // Global interrupt enable
}

// ============================================================================
// Main entry point
// ============================================================================

int main() {
    system_init();
    
    // Read RTC to clear shift register (double-read per firmware)
    uint8_t rtc_buf[7];
    rtc_read_52bits(rtc_buf);
    rtc_read_52bits(rtc_buf);
    
    g_state = STATE_IDLE;
    
    while (1) {
        if (g_state == STATE_IDLE) {
            // Sleep until Timer2 Compare A wakes the CPU
            set_sleep_mode(SLEEP_MODE_PWR_DOWN);
            sleep_mode();
            // On wake, ISR will handle state transition
        }
        else if (g_state == STATE_INTRUSION) {
            target_init();
            g_state = STATE_ACTIVE;
        }
        else if (g_state == STATE_ACTIVE) {
            if (!check_intrusion()) {
                g_state = STATE_IDLE;
            }
            // Long delay mimicking firmware loop
            for (volatile uint32_t i = 1599999; i > 0; i--);
        }
        else {
            g_state = STATE_IDLE;
        }
    }
}
