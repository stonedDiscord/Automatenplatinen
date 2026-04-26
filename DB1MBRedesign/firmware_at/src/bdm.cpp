#include <avr/io.h>
#include <stdint.h>
#include <stdbool.h>

#include "bdm.h"

// ============================================================================
// BDM low-level bit-bang transport
// ============================================================================

static inline uint16_t bdm_transfer(uint16_t data_out)
{
    uint16_t recv = 0;
    // 16 bits, MSB-first. Firmware uses 5 NOPs between edges.
    for (int8_t i = 15; i >= 0; i--)
    {
        bool bit_out = (data_out >> i) & 1;
        // Ensure DSCLK and DSI low before starting bit
        PORTC &= ~((1 << BDM_DSCLK_PIN) | (1 << BDM_DSI_PIN));
        // Delay: ~3 cycles setup
        __asm__ __volatile__("nop\n\tnop\n\tnop");
        if (bit_out)
        {
            PORTC |= (1 << BDM_DSI_PIN);
        }
        // Delay: total 5 NOPs before clock rise (per firmware)
        __asm__ __volatile__("nop\n\tnop\n\tnop\n\tnop");
        // Clock high — DSO sampled on rising edge by target
        PORTC |= (1 << BDM_DSCLK_PIN);
        // Sample DSO after short delay (per firmware pattern)
        __asm__ __volatile__("nop\n\tnop");
        if (PIND & (1 << BDM_DSO_PIN))
        {
            recv |= (1 << i);
        }
        // Complete cycle, clock low for next bit
        __asm__ __volatile__("nop\n\tnop");
        PORTC &= ~(1 << BDM_DSCLK_PIN);
    }
    // Ensure DSI low when idle
    PORTC &= ~(1 << BDM_DSI_PIN);
    return recv;
}

// ============================================================================
// BDM high-level memory operations
// ============================================================================

void bdm_write_word(uint32_t addr, uint16_t data)
{
    // BDM_WRITE | SIZE_WORD = 0x1840
    bdm_transfer(BDM_WRITE | SIZE_WORD);
    bdm_transfer(addr >> 16);
    bdm_transfer(addr & 0xFFFF);
    bdm_transfer(data);
}

uint16_t bdm_read_word(uint32_t addr)
{
    // BDM_READ | SIZE_WORD = 0x1940
    bdm_transfer(BDM_READ | SIZE_WORD);
    bdm_transfer(addr >> 16);
    bdm_transfer(addr & 0xFFFF);
    return bdm_transfer(0x0000);
}

void bdm_write_long(uint32_t addr, uint32_t data)
{
    // BDM_WRITE | SIZE_LONG = 0x1880
    bdm_transfer(BDM_WRITE | SIZE_LONG);
    bdm_transfer(addr >> 16);
    bdm_transfer(addr & 0xFFFF);
    bdm_transfer(data >> 16);
    bdm_transfer(data & 0xFFFF);
}

uint32_t bdm_read_long(uint32_t addr)
{
    // BDM_READ | SIZE_LONG = 0x1980
    bdm_transfer(BDM_READ | SIZE_LONG);
    bdm_transfer(addr >> 16);
    bdm_transfer(addr & 0xFFFF);
    uint16_t high = bdm_transfer(0x0000);
    uint16_t low = bdm_transfer(0x0000);
    return ((uint32_t)high << 16) | low;
}

// Alias for backwards compatibility
uint32_t bdm_read_cmd_long(uint32_t addr)
{
    return bdm_read_long(addr);
}
