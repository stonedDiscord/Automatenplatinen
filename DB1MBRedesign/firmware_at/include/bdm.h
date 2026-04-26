#ifndef BDM_H
#define BDM_H

// BDM pin mappings
#define BDM_DSCLK_PIN   0   // PC0
#define BDM_DSI_PIN     3   // PC3
#define BDM_DSO_PIN     6   // PD6

// Operand Size
#define SIZE_BYTE      0b00000000
#define SIZE_WORD      0b01000000
#define SIZE_LONG      0b10000000
#define SIZE_RESERVED  0b11000000

// Read/Write Memory Location commands
#define BDM_READ        0b0001100100000000  // 0x1900 base; low address byte ORed in
#define BDM_WRITE       0b0001100000000000  // 0x1800 base

// Specific forms:
//  Word write: BDM_WRITE|SIZE_WORD  (0x1840)
//  Word read:  BDM_READ |SIZE_WORD  (0x1940)
//  Long  write: BDM_WRITE|SIZE_LONG  (0x1880) — FUN_code_00024e
//  Long  read:  BDM_READ |SIZE_LONG  (0x1980) — mirror of long write

// Other BDM commands (not used here)
#define BDM_RAREG       0b0010000110000000
#define BDM_WAREG       0b0010000010000000
#define BDM_RSREG       0b0010010010000000
#define BDM_WSREG       0b0010010010000000
#define BDM_DUMP        0b0001110100000000
#define BDM_FILL        0b0001110000000000
#define BDM_GO          0b0000110000000000
#define BDM_CALL        0b0000100000000000
#define BDM_RST         0b0000010000000000
#define BDM_NOP         0b0000000000000000

// System register selects (used with RSREG/WSREG)
#define BDM_RPC         0b0000
#define BDMPCC          0b0001
#define RSR            0b1011
#define USP            0b1100
#define SSP            0b1101
#define SFC            0b1110
#define DFC            0b1111
#define ATEMP          0b1000
#define FAR            0b1001
#define VBR            0b1010

// High-level BDM memory operations
uint16_t bdm_read_word(uint32_t addr);
void    bdm_write_word(uint32_t addr, uint16_t data);
uint32_t bdm_read_long(uint32_t addr);
void    bdm_write_long(uint32_t addr, uint32_t data);

// Compatibility wrapper used by rtc.c
uint32_t bdm_read_cmd_long(uint32_t addr);

#endif // BDM_H
