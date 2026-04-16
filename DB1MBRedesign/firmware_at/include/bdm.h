// BDM Command Codes and Constants

// Operand Size
#define SIZE_BYTE 0b00000000
#define SIZE_WORD 0b01000000
#define SIZE_LONG 0b10000000
#define SIZE_RESERVED 0b11000000

// Read/Write A/D Register
#define BDM_RAREG 0b0010000110000000
#define BDM_WAREG 0b0010000010000000

// Read/Write System Register
#define BDM_RSREG 0b0010010010000000
#define BDM_WSREG 0b0010010010000000
// System registers
#define RPC   0b0000
#define PCC   0b0001
#define SR    0b1011
#define USP   0b1100
#define SSP   0b1101
#define SFC   0b1110
#define DFC   0b1111
#define ATEMP 0b1000
#define FAR   0b1001
#define VBR   0b1010

// Read/Write Memory Location
#define BDM_READ  0b0001100100000000
#define BDM_WRITE 0b0001100000000000

// Dump/Fill Memory Block
#define BDM_DUMP   0b0001110100000000
#define BDM_FILL   0b0001110000000000

// Resume Execution
#define BDM_GO 0b0000110000000000

// Call User Code
#define BDM_CALL 0b0000100000000000

// Reset Peripherals
#define BDM_RST 0b0000010000000000

// No Operation
#define BDM_NOP 0b0000000000000000
