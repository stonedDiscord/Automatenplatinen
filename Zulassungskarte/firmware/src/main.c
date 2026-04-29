/**
 * ATmega48P SPI Slave Firmware
 * Decompiled and improved for readability.
 */

#include <avr/io.h>
#include <avr/interrupt.h>
#include <avr/wdt.h>
#include <avr/eeprom.h>
#include <util/delay.h>
#include <stdint.h>
#include <stdbool.h>

// --- Configuration ---

#define MOSI_PIN PB3
#define MISO_PIN PB4
#define SCK_PIN  PB5

// Command codes received from SPI Master
enum Command {
    CMD_INIT      = 0x31,
    CMD_EE_READ   = 0x32,
    CMD_EE_WRITE  = 0x33,
    CMD_TRANSFORM = 0x34,
    CMD_EE_WRITE_DIRECT = 0x35,
    CMD_EE_READ_DIRECT  = 0x36
};

static const uint8_t XOR_KEY_A[] = {0x33, 0xfb, 0xc7, 0x52, 0xc9};
static const uint8_t XOR_KEY_B[] = {0x29, 0x91, 0xa7, 0xf1, 0x6b};
static const uint8_t XOR_KEY_C[] = {0x8e, 0x65, 0xe1, 0xa3, 0x74, 0x33};
static const uint8_t XOR_KEY_D[] = {0x1d, 0xe9, 0x43, 0x3f, 0xb8, 0x29};

// --- Global State ---

typedef struct {
    // Mapping to registers based on disassembly:
    // bytes[0..5]   -> Zhi, Zlo, Yhi, Ylo, Xhi, Xlo (R31..R26)
    // bytes[6]      -> R25
    // bytes[7..10]  -> R24, R23, R22, R21
    uint8_t bytes[11];
} CryptoState;

static CryptoState g_state;

// --- SPI Bit-Banging Helpers ---

static inline void set_miso_high() { PORTB |= (1 << MISO_PIN); }
static inline void set_miso_low()  { PORTB &= ~(1 << MISO_PIN); }
static inline bool is_mosi_high() { return PINB & (1 << MOSI_PIN); }

/**
 * Corresponds to PCINT1 in disassembly.
 * A fixed delay loop using R17 and R18.
 */
static void spi_delay() {
    for (uint8_t r18 = 0; r18 < 2; r18++) {
        for (uint16_t r17 = 0; r17 < 256; r17++) {
            asm volatile("nop");
        }
    }
}

/**
 * Corresponds to INT0 in disassembly.
 * Signals ready by setting MISO high and waiting for MOSI to go high.
 */
static void ready_and_wait() {
    set_miso_high();
    while (!is_mosi_high()) {
        wdt_reset();
    }
}

/**
 * Corresponds to TIMER3_COMPA in disassembly.
 * Bit-bangs receiving a byte over SPI.
 */
static uint8_t spi_receive_byte() {
    uint8_t result = 0;
    for (uint8_t i = 0; i < 8; i++) {
        wdt_reset();
        spi_delay();
        result <<= 1;
        if (is_mosi_high()) {
            result |= 1;
        }
        // Disassembly toggles MISO pin here as a side effect or feedback
        if (PINB & (1 << MISO_PIN)) {
            set_miso_low();
        } else {
            set_miso_high();
        }
    }
    return result;
}

/**
 * Corresponds to TWI in disassembly.
 * Bit-bangs sending a byte over SPI.
 */
static void spi_send_byte(uint8_t data) {
    for (uint8_t i = 0; i < 8; i++) {
        wdt_reset();
        if (data & 0x80) {
            set_miso_high();
        } else {
            set_miso_low();
        }
        data <<= 1;
        spi_delay(); // Wait for clock edge
    }
}

// --- Crypto Operations ---

static uint8_t transform_byte_a(uint8_t val) {
    uint8_t res = 0;
    uint8_t mask = 0x25;
    for (uint8_t i = 0; i < 8; i++) {
        res <<= 1;
        if (mask & 0x80) res += val;
        mask <<= 1;
    }
    return res + 5;
}

static uint8_t transform_byte_b(uint8_t val) {
    uint8_t res = 0;
    uint8_t mask = 0xAD;
    for (uint8_t i = 0; i < 8; i++) {
        res <<= 1;
        if (mask & 0x80) res += val;
        mask <<= 1;
    }
    return res + 0x9F;
}

static void rotate_left_11() {
    bool carry = (g_state.bytes[10] & 0x80) != 0;
    for (int i = 10; i > 0; i--) {
        g_state.bytes[i] = (g_state.bytes[i] << 1) | (g_state.bytes[i-1] >> 7);
    }
    g_state.bytes[0] = (g_state.bytes[0] << 1) | (carry ? 1 : 0);
}

static void rotate_left_5() {
    bool carry = (g_state.bytes[10] & 0x80) != 0;
    for (int i = 10; i > 6; i--) {
        g_state.bytes[i] = (g_state.bytes[i] << 1) | (g_state.bytes[i-1] >> 7);
    }
    g_state.bytes[6] = (g_state.bytes[6] << 1) | (carry ? 1 : 0);
}

static void rotate_right_6() {
    bool carry = (g_state.bytes[5] & 0x01) != 0;
    for (int i = 5; i < 10; i++) {
        g_state.bytes[i] = (g_state.bytes[i] >> 1) | (g_state.bytes[i+1] << 7);
    }
    g_state.bytes[10] = (g_state.bytes[10] >> 1) | (carry ? 0x80 : 0);
}

static void xor_state_upper(const uint8_t* key) {
    for (int i = 0; i < 5; i++) {
        g_state.bytes[10-i] ^= key[i];
    }
}

static void xor_state_lower(const uint8_t* key) {
    for (int i = 0; i < 6; i++) {
        g_state.bytes[5-i] ^= key[i];
    }
}

static void set_clock_speed(bool fast) {
    CLKPR = 0x80;
    CLKPR = fast ? 0x00 : 0x03; // Div 1 or Div 8
}

// --- Command Handlers ---

static void handle_init() {
    spi_receive_byte(); // Dummy
    spi_delay();
    set_miso_low();

    // Load 7 bytes from EEPROM 0x40..0x46 into bytes[6..0]
    for (int i = 0; i < 7; i++) {
        g_state.bytes[6-i] = eeprom_read_byte((uint8_t*)(uint16_t)(0x40 + i));
    }

    set_clock_speed(true);
    xor_state_lower(XOR_KEY_D);

    for (int r = 0; r < 0x32; r++) {
        wdt_reset();
        for (int i = 0; i < 6; i++) {
            g_state.bytes[i] = transform_byte_a(g_state.bytes[i]);
        }
        for (int i = 0; i < 3; i++) {
            rotate_left_11();
        }
    }

    xor_state_upper(XOR_KEY_A);
    xor_state_lower(XOR_KEY_C);
    set_clock_speed(false);

    ready_and_wait();
    for (int i = 0; i < 6; i++) {
        spi_send_byte(g_state.bytes[5-i]);
    }
    set_miso_low();
}

static void handle_ee_read() {
    spi_receive_byte(); // Dummy
    uint8_t addr = spi_receive_byte();
    spi_delay();
    set_miso_low();

    g_state.bytes[6] = eeprom_read_byte((uint8_t*)(uint16_t)addr);

    set_clock_speed(true);
    xor_state_upper(XOR_KEY_B);

    for (int r = 0; r < 0x32; r++) {
        wdt_reset();
        for (int i = 0; i < 3; i++) {
            rotate_left_5();
        }
    }

    xor_state_upper(XOR_KEY_A);
    set_clock_speed(false);

    ready_and_wait();
    for (int i = 0; i < 5; i++) {
        spi_send_byte(g_state.bytes[6+i]);
    }
    set_miso_low();
}

static void handle_ee_write(uint8_t challenge[4]) {
    ready_and_wait();
    for (int i = 0; i < 4; i++) {
        spi_send_byte(challenge[i]);
    }

    set_miso_low();
    spi_delay();

    // Wait for master response (MOSI high)
    bool timeout = true;
    for (int i = 0; i < 0x32; i++) {
        wdt_reset();
        if (is_mosi_high()) {
            timeout = false;
            break;
        }
        spi_delay();
    }
    if (timeout) return;

    set_miso_high();
    spi_receive_byte(); // Dummy
    g_state.bytes[6] = spi_receive_byte();
    g_state.bytes[5] = spi_receive_byte();
    // In disassembly, bytes[4] might also be received or set.
    // Based on XOR logic, it seems bytes[5,4] are used.
    g_state.bytes[4] = spi_receive_byte(); 
    set_miso_low();

    set_clock_speed(true);
    xor_state_upper(XOR_KEY_A);
    g_state.bytes[5] ^= 0x8E;
    g_state.bytes[4] ^= 0x65;

    for (int r = 0; r < 0x32; r++) {
        wdt_reset();
        for (int i = 0; i < 3; i++) {
            rotate_right_6();
        }
        for (int i = 5; i <= 10; i++) {
            g_state.bytes[i] = transform_byte_b(g_state.bytes[i]);
        }
    }

    xor_state_upper(XOR_KEY_B);
    g_state.bytes[5] ^= 0x1D;
    set_clock_speed(false);

    // Verify challenge against state
    if (challenge[0] == g_state.bytes[10] &&
        challenge[1] == g_state.bytes[9] &&
        challenge[2] == g_state.bytes[8] &&
        challenge[3] == g_state.bytes[7] &&
        g_state.bytes[6] < 0x40) {
        eeprom_write_byte((uint8_t*)(uint16_t)g_state.bytes[6], g_state.bytes[5]);
    }
    set_miso_low();
}

static void handle_transform() {
    for (int i = 0; i < 4; i++) {
        g_state.bytes[10-i] = spi_receive_byte();
    }
    set_miso_low();

    // Load from EEPROM 0x4B
    uint8_t check = eeprom_read_byte((uint8_t*)0x4B);
    if (check != 0) {
        // Load 7 bytes from 0x40 to 0x46 (again?)
        // Disassembly: rcall FUN_code_000007 many times.
        for (int i = 0; i < 7; i++) {
            g_state.bytes[6-i] = eeprom_read_byte((uint8_t*)(uint16_t)(0x40 + i));
        }
    }

    set_clock_speed(true);
    xor_state_upper(XOR_KEY_B);
    xor_state_lower(XOR_KEY_D);

    for (int r = 0; r < 0x32; r++) {
        wdt_reset();
        for (int i = 0; i < 6; i++) {
            g_state.bytes[i] = transform_byte_a(g_state.bytes[i]);
        }
        for (int i = 0; i < 3; i++) {
            rotate_left_11();
        }
    }

    xor_state_upper(XOR_KEY_A);
    xor_state_lower(XOR_KEY_C);
    set_clock_speed(false);

    ready_and_wait();
    for (int i = 0; i < 6; i++) {
        spi_send_byte(g_state.bytes[5-i]);
    }
    set_miso_low();
}

static void handle_ee_write_direct() {
    uint8_t addr = spi_receive_byte();
    if (addr >= 0x20 && addr < 0x40) {
        uint8_t val = spi_receive_byte();
        eeprom_write_byte((uint8_t*)(uint16_t)addr, val);
    }
    spi_delay();
    set_miso_low();
}

static void handle_ee_read_direct() {
    uint8_t addr = spi_receive_byte();
    if (addr >= 0x20 && addr < 0x40) {
        uint8_t val = eeprom_read_byte((uint8_t*)(uint16_t)addr);
        ready_and_wait();
        spi_send_byte(val);
    }
    set_miso_low();
}

// --- Main Entry ---

void init_hardware() {
    set_clock_speed(false);
    DDRD = 0xFF;
    DDRC = 0xFF;
    PORTD = 0;
    PORTC = 0;
    PORTB = 0;
    DDRB = 0xF7; // PB3 (MOSI) as input, others as output

    // Watchdog Setup
    WDTCSR |= (1 << WDCE) | (1 << WDE);
    WDTCSR = (1 << WDE); // Enable watchdog, 16ms timeout
}

int main() {
    init_hardware();

    uint8_t challenge[4] = {0, 0, 0, 0};

    while (true) {
        // Main Loop: Generate challenge and wait for Master
        while (!is_mosi_high()) {
            wdt_reset();
            challenge[0]++;
            if (challenge[0] == 0) {
                challenge[1]++;
            }
            challenge[2]--;
            if (challenge[2] == 0xFF) { // Underflow
                challenge[3]++;
            }
        }

        set_miso_high();
        uint8_t cmd = spi_receive_byte();

        switch (cmd) {
            case CMD_INIT:      handle_init(); break;
            case CMD_EE_READ:   handle_ee_read(); break;
            case CMD_EE_WRITE:  handle_ee_write(challenge); break;
            case CMD_TRANSFORM: handle_transform(); break;
            case CMD_EE_WRITE_DIRECT: handle_ee_write_direct(); break;
            case CMD_EE_READ_DIRECT:  handle_ee_read_direct(); break;
            default:
                set_miso_low();
                break;
        }

        wdt_reset();
    }

    return 0;
}
