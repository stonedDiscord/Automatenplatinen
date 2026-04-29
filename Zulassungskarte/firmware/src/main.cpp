#include <avr/eeprom.h>
#include <avr/io.h>
#include <avr/wdt.h>
#include <stdbool.h>
#include <stdint.h>

// PORTB pin assignments
#define MOSI_PIN PB3
#define MISO_PIN PB4
#define SCK_PIN  PB5

// Command states received over SPI
#define STATE_INIT      0x31
#define STATE_EE_READ   0x32
#define STATE_EE_WRITE  0x33
#define STATE_TRANSFORM 0x34
#define STATE_EE_READ2  0x35
#define STATE_EE_READ3  0x36

static const uint8_t XOR_KEY_A[] = {0x33, 0xfb, 0xc7, 0x52, 0xc9};
static const uint8_t XOR_KEY_B[] = {0x29, 0x91, 0xa7, 0xf1, 0x6b};
static const uint8_t XOR_KEY_C[] = {0x8e, 0x65, 0xe1, 0xa3, 0x74, 0x33};
static const uint8_t XOR_KEY_D[] = {0x1d, 0xe9, 0x43, 0x3f, 0xb8, 0x29};

typedef struct {
    uint8_t bytes[11];
} CryptoState;

static CryptoState g_crypto;

static inline void setMisoHigh(void) {
    PORTB |= (1 << MISO_PIN);
}

static inline void setMisoLow(void) {
    PORTB &= ~(1 << MISO_PIN);
}

static inline bool isMosiHigh(void) {
    return PINB & (1 << MOSI_PIN);
}

static inline bool isClockHigh(void) {
    return PINB & (1 << SCK_PIN);
}

static void waitForClockLevel(bool high) {
    while (isClockHigh() != high) {
        wdt_reset();
    }
}

static void waitForMasterRequest(void) {
    while (!isMosiHigh()) {
        wdt_reset();
    }
}

static void setClockDiv8(void) {
    CLKPR = 0x80;
    CLKPR = 0x03;
}

static void setClockDiv1(void) {
    CLKPR = 0x80;
    CLKPR = 0x00;
}

static uint8_t receiveSpiByte(void) {
    uint8_t result = 0;

    for (uint8_t bit = 0; bit < 8; bit++) {
        wdt_reset();
        waitForClockLevel(false);
        waitForClockLevel(true);
        result = (result << 1) | (isMosiHigh() ? 1 : 0);
    }

    return result;
}

static void sendSpiByte(uint8_t value) {
    for (uint8_t bit = 0; bit < 8; bit++) {
        wdt_reset();
        if (value & 0x80) {
            setMisoHigh();
        } else {
            setMisoLow();
        }
        value <<= 1;
        waitForClockLevel(false);
        waitForClockLevel(true);
    }
    setMisoLow();
}

static uint8_t transformByteA(uint8_t input) {
    uint8_t result = 0;
    uint8_t mask = 0x25;

    for (uint8_t i = 0; i < 8; i++) {
        result <<= 1;
        if (mask & 0x80) {
            result += input;
        }
        mask <<= 1;
    }

    return result + 5;
}

static uint8_t transformByteB(uint8_t input) {
    uint8_t result = 0;
    uint8_t mask = 0xad;

    for (uint8_t i = 0; i < 8; i++) {
        result <<= 1;
        if (mask & 0x80) {
            result += input;
        }
        mask <<= 1;
    }

    return result + 0x9f;
}

static void rotateStateLeft11(void) {
    uint8_t carry = 0;

    for (uint8_t index = 0; index < 11; index++) {
        uint8_t value = g_crypto.bytes[index];
        g_crypto.bytes[index] = (value << 1) | carry;
        carry = value >> 7;
    }

    if (carry) {
        g_crypto.bytes[0] |= 0x01;
    }
}

static void rotateStateLeft5(void) {
    uint8_t carry = 0;

    for (uint8_t index = 6; index <= 10; index++) {
        uint8_t value = g_crypto.bytes[index];
        g_crypto.bytes[index] = (value << 1) | carry;
        carry = value >> 7;
    }

    if (carry) {
        g_crypto.bytes[6] |= 0x01;
    }
}

static void rotateStateRight6(void) {
    uint8_t carry = 0;

    for (int index = 10; index >= 5; index--) {
        uint8_t value = g_crypto.bytes[index];
        g_crypto.bytes[index] = (value >> 1) | (carry << 7);
        carry = value & 1;
    }

    if (carry) {
        g_crypto.bytes[10] |= 0x80;
    }
}

static void xorUpperState(const uint8_t *key, uint8_t keySize) {
    for (uint8_t i = 0; i < keySize; i++) {
        g_crypto.bytes[10 - i] ^= key[i];
    }
}

static void xorLowerState(const uint8_t *key, uint8_t keySize) {
    for (uint8_t i = 0; i < keySize; i++) {
        g_crypto.bytes[5 - i] ^= key[i];
    }
}

static void loadEepromReverse(uint8_t firstAddress, uint8_t destIndex, uint8_t count) {
    for (uint8_t offset = 0; offset < count; offset++) {
        g_crypto.bytes[destIndex - offset] = eeprom_read_byte((uint8_t*)(uint16_t)(firstAddress + offset));
    }
}

static void sendStateBytesAscending(uint8_t startIndex, uint8_t count) {
    for (uint8_t i = 0; i < count; i++) {
        sendSpiByte(g_crypto.bytes[startIndex + i]);
    }
}

static void sendStateBytesDescending(uint8_t startIndex, uint8_t count) {
    for (uint8_t i = 0; i < count; i++) {
        sendSpiByte(g_crypto.bytes[startIndex - i]);
    }
}

static bool isSafeEepromAddress(uint8_t address) {
    return (address >= 0x20 && address < 0x40);
}

static void initializeCryptoState(void) {
    loadEepromReverse(0x40, 6, 7);
    setClockDiv1();
    xorLowerState(XOR_KEY_D, sizeof(XOR_KEY_D));

    for (uint8_t round = 0; round < 0x32; round++) {
        wdt_reset();
        for (uint8_t index = 0; index < 6; index++) {
            g_crypto.bytes[5 - index] = transformByteA(g_crypto.bytes[5 - index]);
        }
        for (uint8_t rotate = 0; rotate < 3; rotate++) {
            rotateStateLeft11();
        }
    }

    xorUpperState(XOR_KEY_A, sizeof(XOR_KEY_A));
    xorLowerState(XOR_KEY_C, sizeof(XOR_KEY_C));
    setClockDiv8();
    sendStateBytesDescending(5, 6);
    setMisoLow();
}

static void readEncryptedEepromValue(void) {
    receiveSpiByte(); // dummy byte accepted from master
    uint8_t address = receiveSpiByte();
    g_crypto.bytes[6] = eeprom_read_byte((uint8_t*)(uint16_t)address);

    setClockDiv1();
    xorUpperState(XOR_KEY_B, sizeof(XOR_KEY_B));

    for (uint8_t round = 0; round < 0x32; round++) {
        wdt_reset();
        for (uint8_t rotate = 0; rotate < 3; rotate++) {
            rotateStateLeft5();
        }
    }

    xorUpperState(XOR_KEY_A, sizeof(XOR_KEY_A));
    setClockDiv8();
    sendStateBytesAscending(6, 5);
    setMisoLow();
}

static void verifyAndWriteEeprom(uint8_t challenge[4]) {
    setMisoLow();
    wdt_reset();
    setMisoHigh();
    waitForMasterRequest();

    for (uint8_t i = 0; i < 4; i++) {
        sendSpiByte(challenge[i]);
    }

    bool gotResponse = false;
    for (uint8_t timeout = 0; timeout < 0x32; timeout++) {
        wdt_reset();
        if (isMosiHigh()) {
            gotResponse = true;
            break;
        }
    }

    if (!gotResponse) {
        setMisoLow();
        return;
    }

    setMisoHigh();
    g_crypto.bytes[6] = receiveSpiByte();
    g_crypto.bytes[5] = receiveSpiByte();
    g_crypto.bytes[4] = receiveSpiByte();
    setMisoLow();

    setClockDiv1();
    xorUpperState(XOR_KEY_A, sizeof(XOR_KEY_A));
    g_crypto.bytes[5] ^= 0x8e;
    g_crypto.bytes[4] ^= 0x65;

    for (uint8_t round = 0; round < 0x32; round++) {
        wdt_reset();
        rotateStateRight6();
        for (uint8_t index = 5; index <= 10; index++) {
            g_crypto.bytes[index] = transformByteB(g_crypto.bytes[index]);
        }
    }

    xorUpperState(XOR_KEY_B, sizeof(XOR_KEY_B));
    g_crypto.bytes[5] ^= 0x1d;
    setClockDiv8();

    if (challenge[0] == g_crypto.bytes[10]
        && challenge[1] == g_crypto.bytes[9]
        && challenge[2] == g_crypto.bytes[8]
        && challenge[3] == g_crypto.bytes[7]
        && g_crypto.bytes[6] < 0x40) {
        eeprom_write_byte((uint8_t*)(uint16_t)g_crypto.bytes[6], g_crypto.bytes[5]);
    }

    setMisoLow();
}

static void transformCommand(void) {
    for (int index = 10; index >= 7; index--) {
        g_crypto.bytes[index] = receiveSpiByte();
    }
    setMisoLow();

    loadEepromReverse(0x47, 6, 7);
    setClockDiv1();
    xorUpperState(XOR_KEY_B, sizeof(XOR_KEY_B));
    xorLowerState(XOR_KEY_D, sizeof(XOR_KEY_D));

    for (uint8_t round = 0; round < 0x32; round++) {
        wdt_reset();
        for (uint8_t index = 0; index < 6; index++) {
            g_crypto.bytes[5 - index] = transformByteA(g_crypto.bytes[5 - index]);
        }
        for (uint8_t rotate = 0; rotate < 3; rotate++) {
            rotateStateLeft11();
        }
    }

    xorUpperState(XOR_KEY_A, sizeof(XOR_KEY_A));
    xorLowerState(XOR_KEY_C, sizeof(XOR_KEY_C));
    setClockDiv8();
    sendStateBytesDescending(5, 6);
    setMisoLow();
}

static void writeEepromDirect(void) {
    uint8_t address = receiveSpiByte();
    if (!isSafeEepromAddress(address)) {
        setMisoLow();
        return;
    }

    receiveSpiByte();
    uint8_t value = receiveSpiByte();
    eeprom_write_byte((uint8_t*)(uint16_t)address, value);
    setMisoLow();
}

static void readEepromDirect(void) {
    uint8_t address = receiveSpiByte();
    if (!isSafeEepromAddress(address)) {
        setMisoLow();
        return;
    }

    uint8_t value = eeprom_read_byte((uint8_t*)(uint16_t)address);
    setMisoLow();
    setMisoHigh();
    waitForMasterRequest();
    sendSpiByte(value);
    setMisoLow();
}

void init_hardware(void) {
    setClockDiv8();
    DDRD = 0xFF;
    DDRC = 0xFF;
    PORTD = 0;
    PORTC = 0;
    PORTB = 0;
    DDRB = 0xF7; // PB3 input, other pins output

    WDTCSR |= (1 << WDCE) | (1 << WDE);
    WDTCSR = (1 << WDE);
}

int main(void) {
    init_hardware();

    uint8_t challenge[4] = {0, 0, 0, 0};

    for (;;) {
        while (!isMosiHigh()) {
            wdt_reset();
            challenge[0]++;
            if (challenge[0] == 0) {
                challenge[1]++;
            }
            if (challenge[2]-- == 0) {
                challenge[3]++;
            }
        }

        setMisoHigh();
        uint8_t command = receiveSpiByte();

        switch (command) {
            case STATE_INIT:
                initializeCryptoState();
                break;

            case STATE_EE_READ:
                readEncryptedEepromValue();
                break;

            case STATE_EE_WRITE:
                verifyAndWriteEeprom(challenge);
                break;

            case STATE_TRANSFORM:
                transformCommand();
                break;

            case STATE_EE_READ2:
                writeEepromDirect();
                break;

            case STATE_EE_READ3:
                readEepromDirect();
                break;

            default:
                setMisoLow();
                break;
        }

        wdt_reset();
    }
}
