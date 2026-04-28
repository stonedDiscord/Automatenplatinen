#include <avr/eeprom.h>
#include <avr/io.h>
#include <avr/wdt.h>

/*
PINS
PORTB:
PB3 MOSI (Input)
PB4 MISO (Output)
PB5 SCK (Input)
*/

// ─── State constants ───
#define STATE_INIT      0x31
#define STATE_EE_READ   0x32
#define STATE_EE_WRITE  0x33
#define STATE_TRANSFORM 0x34
#define STATE_EE_READ2  0x35
#define STATE_EE_READ3  0x36

// ─── XOR decryption keys ───
static const uint8_t XOR_KEY_A[] = {0x33, 0xfb, 0xc7, 0x52, 0xc9};
static const uint8_t XOR_KEY_B[] = {0x29, 0x91, 0xa7, 0xf1, 0x6b};
static const uint8_t XOR_KEY_C[] = {0x8e, 0x65, 0xe1, 0xa3, 0x74, 0x33};
static const uint8_t XOR_KEY_D[] = {0x1d, 0xe9, 0x43, 0x3f, 0xb8, 0x29};

// ─── Data buffers ───
typedef struct {
    uint8_t bytes[11]; 
    // 0: Zhi, 1: Zlo, 2: Yhi, 3: Ylo, 4: Xhi, 5: Xlo, 6: R25, 7: R24, 8: R23, 9: R22, 10: R21
} CryptoState;

static CryptoState g_crypto;

// ─── GPIO Helpers ───
static void misoHigh(void) { PORTB |= (1 << 4); }
static void misoLow(void) { PORTB &= ~(1 << 4); }

static void waitPinB3High(void) {
    while (!(PINB & (1 << 3))) { wdt_reset(); }
}

// ─── Clock Prescaler ───
static void setClockDiv8(void) {
    CLKPR = 0x80;
    CLKPR = 0x03;
}

static void setClockDiv1(void) {
    CLKPR = 0x80;
    CLKPR = 0x00;
}

// ─── TWI (Bitbang) ───
static void twiSendByte(uint8_t data) {
    for (int i = 0; i < 8; i++) {
        wdt_reset();
        // Disassembly 0x004e logic:
        // shift left, send MSB... 
    }
}

// ─── SPI (Bitbang) ───
static uint8_t spiReceiveByte(void) {
    uint8_t data = 0;
    for (int i = 0; i < 8; i++) {
        wdt_reset();
        data <<= 1;
        if (PINB & (1 << 3)) {
            data |= 1;
        }
    }
    return data;
}

// ─── Crypto Primitives ───
static uint8_t transformByte(uint8_t in) {
    uint8_t out = 0;
    uint8_t mask = 0x25;
    for (int i = 0; i < 8; i++) {
        out += out;
        uint8_t old_mask = mask;
        mask += mask;
        if (old_mask & 0x80) out += in;
    }
    out += 5;
    return out;
}

static uint8_t transformByteB(uint8_t in) {
    uint8_t out = 0;
    uint8_t mask = 0xad;
    for (int i = 0; i < 8; i++) {
        out += out;
        uint8_t old_mask = mask;
        mask += mask;
        if (old_mask & 0x80) out += in;
    }
    out += 0x9f;
    return out;
}

static void shiftLeft11(void) {
    uint8_t carry = 0;
    for (int i = 0; i < 11; i++) {
        uint8_t val = g_crypto.bytes[i];
        g_crypto.bytes[i] = (val << 1) | carry;
        carry = (val >> 7) & 1;
    }
    if (carry) g_crypto.bytes[0] |= 0x01;
}

static void shiftLeft5(void) {
    uint8_t carry = 0;
    for (int i = 6; i <= 10; i++) {
        uint8_t val = g_crypto.bytes[i];
        g_crypto.bytes[i] = (val << 1) | carry;
        carry = (val >> 7) & 1;
    }
    if (carry) g_crypto.bytes[6] |= 0x01;
}

static void shiftRight6(void) {
    uint8_t carry = 0;
    for (int i = 10; i >= 5; i--) {
        uint8_t val = g_crypto.bytes[i];
        g_crypto.bytes[i] = (val >> 1) | (carry << 7);
        carry = val & 1;
    }
    if (carry) g_crypto.bytes[10] |= 0x80;
}

static void applyXorKeyA(void) {
    for (int i = 0; i < 5; i++) g_crypto.bytes[10 - i] ^= XOR_KEY_A[i];
}

static void applyXorKeyB(void) {
    for (int i = 0; i < 5; i++) g_crypto.bytes[10 - i] ^= XOR_KEY_B[i];
}

static void applyXorKeyC(void) {
    for (int i = 0; i < 6; i++) g_crypto.bytes[5 - i] ^= XOR_KEY_C[i];
}

static void applyXorKeyD(void) {
    for (int i = 0; i < 6; i++) g_crypto.bytes[5 - i] ^= XOR_KEY_D[i];
}

// ─── Main Logic ───
void init_hardware(void) {
    setClockDiv8();
    DDRD = 0xFF;
    DDRC = 0xFF;
    PORTD = 0;
    PORTC = 0;
    PORTB = 0;
    DDRB = 0xF7; // PB3 input, others output
    
    WDTCSR |= (1 << WDCE) | (1 << WDE);
    WDTCSR = (1 << WDE);
}

int main(void) {
    init_hardware();
    
    uint8_t r0 = 0, r1 = 0, r2 = 0, r3 = 0;
    
    for (;;) {
        // Wait for PINB3 high and accumulate "checksum"
        while (!(PINB & (1 << 3))) {
            wdt_reset();
            r0++;
            if (r0 == 0) r1++;
            uint8_t borrow = (r2 == 0);
            r2--;
            if (borrow) r3++; 
        }
        
        misoHigh();
        uint8_t cmd = spiReceiveByte();
        
        if (cmd == STATE_INIT) {
            uint8_t addr = 0x3f;
            for (int i = 0; i < 7; i++) {
                addr++;
                g_crypto.bytes[6 - i] = eeprom_read_byte((uint8_t*)(uint16_t)addr);
            }
            
            setClockDiv1();
            applyXorKeyD();
            
            for (int i = 0; i < 0x32; i++) {
                wdt_reset();
                for (int j = 0; j < 6; j++) g_crypto.bytes[5 - j] = transformByte(g_crypto.bytes[5 - j]);
                for (int j = 0; j < 3; j++) shiftLeft11();
            }
            
            applyXorKeyA();
            applyXorKeyC();
            setClockDiv8();
            
            for (int i = 0; i < 6; i++) twiSendByte(g_crypto.bytes[5 - i]);
            
            misoLow();
        } 
        else if (cmd == STATE_EE_READ) {
            spiReceiveByte(); // dummy
            uint8_t addr = spiReceiveByte();
            g_crypto.bytes[6] = eeprom_read_byte((uint8_t*)(uint16_t)addr);
            
            setClockDiv1();
            applyXorKeyB();
            
            for (int i = 0; i < 0x32; i++) {
                wdt_reset();
                for (int j = 0; j < 3; j++) shiftLeft5();
            }
            
            applyXorKeyA();
            setClockDiv8();
            
            for (int i = 6; i <= 10; i++) twiSendByte(g_crypto.bytes[i]);
            
            misoLow();
        }
        else if (cmd == STATE_EE_WRITE) {
            misoLow();
            wdt_reset();
            misoHigh(); waitPinB3High();
            twiSendByte(r0); twiSendByte(r1); twiSendByte(r2); twiSendByte(r3);
            
            uint8_t counter = 0x32;
            bool pinHigh = false;
            while (counter--) {
                wdt_reset();
                if (PINB & (1 << 3)) { pinHigh = true; break; }
            }
            
            if (pinHigh) {
                misoHigh();
                g_crypto.bytes[6] = spiReceiveByte(); 
                g_crypto.bytes[5] = spiReceiveByte(); 
                g_crypto.bytes[4] = spiReceiveByte(); 
                misoLow();
                
                setClockDiv1();
                applyXorKeyA();
                g_crypto.bytes[5] ^= 0x8e; 
                g_crypto.bytes[4] ^= 0x65;
                
                for (int i = 0; i < 0x32; i++) {
                    wdt_reset();
                    shiftRight6();
                    for (int j = 5; j <= 10; j++) g_crypto.bytes[j] = transformByteB(g_crypto.bytes[j]);
                }
                
                applyXorKeyB();
                g_crypto.bytes[5] ^= 0x1d; 
                
                setClockDiv8();
                
                if (r0 == g_crypto.bytes[10] && r1 == g_crypto.bytes[9] && 
                    r2 == g_crypto.bytes[8] && r3 == g_crypto.bytes[7]) {
                    if (g_crypto.bytes[6] < 0x40) {
                        eeprom_write_byte((uint8_t*)(uint16_t)g_crypto.bytes[6], g_crypto.bytes[5]);
                    }
                }
            }
            misoLow();
        }
        else if (cmd == STATE_TRANSFORM) {
            for (int i = 10; i >= 7; i--) g_crypto.bytes[i] = spiReceiveByte();
            misoLow();
            
            if (eeprom_read_byte((uint8_t*)0x4b) == 0) {
            }
            
            uint8_t addr = 0x46;
            for (int i = 0; i < 7; i++) {
                addr++;
                g_crypto.bytes[6 - i] = eeprom_read_byte((uint8_t*)(uint16_t)addr);
            }
            
            setClockDiv1();
            applyXorKeyB(); 
            applyXorKeyD(); 
            
            for (int i = 0; i < 0x32; i++) {
                wdt_reset();
                for (int j = 0; j < 6; j++) g_crypto.bytes[5 - j] = transformByte(g_crypto.bytes[5 - j]);
                for (int j = 0; j < 3; j++) shiftLeft11();
            }
            
            applyXorKeyA();
            applyXorKeyC();
            setClockDiv8();
            
            for (int i = 0; i < 6; i++) twiSendByte(g_crypto.bytes[5 - i]);
            misoLow();
        }
        else if (cmd == STATE_EE_READ2) {
            uint8_t addr = spiReceiveByte();
            if (addr >= 0x20 && addr < 0x40) {
                eeprom_read_byte((uint8_t*)(uint16_t)addr);
                uint8_t newVal = spiReceiveByte();
                eeprom_write_byte((uint8_t*)(uint16_t)addr, newVal);
            }
            misoLow();
        }
        else if (cmd == STATE_EE_READ3) {
            uint8_t addr = spiReceiveByte();
            if (addr >= 0x20 && addr < 0x40) {
                uint8_t val = eeprom_read_byte((uint8_t*)(uint16_t)addr);
                misoLow();
                misoHigh(); waitPinB3High();
                twiSendByte(val);
            }
            misoLow();
        }
        else {
            misoLow();
        }
        
        wdt_reset();
    }
}
