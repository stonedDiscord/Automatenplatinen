#include <avr/io.h>

/* Register Definitions */
#define ent0 r0
#define ent1 r1
#define ent2 r2
#define ent3 r3
#define loop_ext r4
#define loop_int r5
#define bsn0 r6
#define bsn1 r7
#define bsn2 r8
#define bsn3 r9
#define zero r10
#define sn0 r12
#define sn1 r13
#define sn2 r14
#define sn3 r15
#define temp r16
#define arg1 r17
#define res  r18
#define cnt  r19
#define flags r20
#define s0 r21
#define s1 r22
#define s2 r23
#define s3 r24
#define s4 r25
#define s5 r26
#define s6 r27
#define s7 r28
#define s8 r29
#define s9 r30
#define s10 r31

/* Serial Number Configuration (Default: Freischalt) */
#ifndef CASE_ID_01
#define CASE_ID_01 0x12
#endif
#ifndef CASE_ID_23
#define CASE_ID_23 0x34
#endif

#ifndef ZL_NUM_0
#define ZL_NUM_0 0x09
#endif
#ifndef ZL_NUM_12
#define ZL_NUM_12 0x99
#endif
#ifndef ZL_NUM_34
#define ZL_NUM_34 0x99
#endif
#ifndef ZL_NUM_56
#define ZL_NUM_56 0x99
#endif
#ifndef ZL_NUM_78
#define ZL_NUM_78 0x99
#endif

#ifndef DATE_0
#define DATE_0 0x01
#endif
#ifndef DATE_1
#define DATE_1 0x98
#endif

.section .text

.global vectors
vectors:
    rjmp reset
    reti

/* Bit-banged Handshake Protocol: Start Transmission */
comm_tx_start:
    sbi	_SFR_IO_ADDR(PORTB), 6
comm_tx_start_wait:
    sbis	_SFR_IO_ADDR(PINB), 5
    rjmp comm_tx_start_wait
    ori	flags, 0x20
    ret

/* EEPROM Access Helpers */
eeprom_read_next:
    inc	temp
    out	_SFR_IO_ADDR(EEAR), temp
    sbi	_SFR_IO_ADDR(EECR), 0
    ret

eeprom_write_wait_and_inc:
    inc	temp
    out	_SFR_IO_ADDR(EEAR), temp
    sbi	_SFR_IO_ADDR(EECR), 1
eeprom_wait_loop:
    sbic	_SFR_IO_ADDR(EECR), 1
    rjmp eeprom_wait_loop
    ret

/* Timing Delay */
comm_delay:
    eor	arg1, arg1
    ldi	res, 0x04
delay_inner_loop:
    dec	arg1
    brne delay_inner_loop
    dec	res
    brne delay_inner_loop
    ret

/* Crypto Key Application */
crypto_apply_key_1:
    ldi	temp, 0x29
    eor	s0, temp
    ldi	temp, 0x91
    eor	s1, temp
    ldi	temp, 0xA7
    eor	s2, temp
    ldi	temp, 0xF1
    eor	s3, temp
    ldi	temp, 0x6B
    eor	s4, temp
    ret

crypto_update_state:
    mov	temp, s0
    rcall crypto_lcg_step_1
    mov	s0, res
    mov	temp, s1
    rcall crypto_lcg_step_1
    mov	s1, res
    mov	temp, s2
    rcall crypto_lcg_step_1
    mov	s2, res
    mov	temp, s3
    rcall crypto_lcg_step_1
    mov	s3, res
    mov	temp, s4
    rcall crypto_lcg_step_1
    mov	s4, res
    ret

/* Communication: Receive State and Bytes */
comm_rx_state:
    rcall comm_rx_byte
    mov	s0, temp
    rcall comm_rx_byte
    mov	s1, temp
    rcall comm_rx_byte
    mov	s2, temp
    rcall comm_rx_byte
    mov	s3, temp
    ret

comm_rx_byte:
    ldi	cnt, 0x08
rx_bit_loop:
    wdr
    rcall comm_delay
    add	temp, temp
    sbic	_SFR_IO_ADDR(PINB), 5
    ori	temp, 0x01
    sbis	_SFR_IO_ADDR(PINB), 6
    rjmp rx_bit_low
    cbi	_SFR_IO_ADDR(PORTB), 6
    rjmp rx_bit_done
rx_bit_low:
    sbi	_SFR_IO_ADDR(PORTB), 6
rx_bit_done:
    dec	cnt
    brne rx_bit_loop
    ret

comm_tx_byte:
    ldi	cnt, 0x08
tx_bit_loop:
    wdr
    add	temp, temp
    brcc tx_bit_low
    sbi	_SFR_IO_ADDR(PORTB), 6
    rjmp tx_bit_done
tx_bit_low:
    cbi	_SFR_IO_ADDR(PORTB), 6
tx_bit_done:
    rcall comm_wait_ack
    dec	cnt
    brne tx_bit_loop
    ret

comm_wait_ack:
    sbrc	flags, 5
    rjmp wait_for_pb5_low
wait_for_pb5_high:
    sbis	_SFR_IO_ADDR(PINB), 5
    rjmp wait_for_pb5_high
    ori	flags, 0x20
    rjmp wait_for_pb5_done
wait_for_pb5_low:
    sbic	_SFR_IO_ADDR(PINB), 5
    rjmp wait_for_pb5_low
    andi	flags, 0xDF
wait_for_pb5_done:
    ret

/* Linear Congruential Generators (LCG) */
crypto_lcg_step_1:
    eor	res, res
    ldi	arg1, 0x25
    ldi	cnt, 0x08
lcg_loop_1:
    add	res, res
    add	arg1, arg1
    brcc lcg_step_1_no_add
    add	res, temp
lcg_step_1_no_add:
    dec	cnt
    brne lcg_loop_1
    ldi	arg1, 0x05
    add	res, arg1
    ret

crypto_lcg_step_2:
    eor	res, res
    ldi	arg1, 0xAD
    ldi	cnt, 0x08
lcg_loop_2:
    add	res, res
    add	arg1, arg1
    brcc lcg_step_2_no_add
    add	res, temp
lcg_step_2_no_add:
    dec	cnt
    brne lcg_loop_2
    ldi	arg1, 0x9F
    add	res, arg1
    ret

crypto_apply_key_2:
    ldi	temp, 0x33
    eor	s0, temp
    ldi	temp, 0xFB
    eor	s1, temp
    ldi	temp, 0xC7
    eor	s2, temp
    ldi	temp, 0x52
    eor	s3, temp
    ldi	temp, 0xC9
    eor	s4, temp
    ret

comm_tx_state:
    mov	temp, s0
    rcall comm_tx_byte
    mov	temp, s1
    rcall comm_tx_byte
    mov	temp, s2
    rcall comm_tx_byte
    mov	temp, s3
    rcall comm_tx_byte
    mov	temp, s4
    rcall comm_tx_byte
    ret

/* System Reset and Initialization */
reset:
    ldi	temp, 0x00
    mov	zero, temp
    ldi	temp, 0x0C
    out	_SFR_IO_ADDR(EEAR), temp
    sbi	_SFR_IO_ADDR(EECR), 0
    in	temp, _SFR_IO_ADDR(EEDR)
    cpi	temp, 0x00
    breq reset_done
    ldi	temp, 0x00
    out	_SFR_IO_ADDR(EEDR), temp
    ldi	temp, 0xFF
    ldi	arg1, 0x40
reset_eeprom_loop:
    rcall eeprom_write_wait_and_inc
    dec	arg1
    brne reset_eeprom_loop
reset_done:
    ldi	temp, 0xFF
    out	_SFR_IO_ADDR(DDRD), temp
    eor	temp, temp
    out	_SFR_IO_ADDR(PORTD), temp
    out	_SFR_IO_ADDR(PORTB), temp
    ldi	temp, 0xDF
    out	_SFR_IO_ADDR(DDRB), temp
    ldi	temp, 0x08
    out	_SFR_IO_ADDR(WDTCR), temp

/* Main Idle Loop */
idle_wait:
    eor	temp, temp
    ldi	arg1, 0x01
entropy_loop:
    wdr
    add	ent0, arg1
    adc	ent1, temp
    sub	ent2, arg1
    adc	ent3, temp
    sbis	_SFR_IO_ADDR(PINB), 5
    rjmp entropy_loop
    sbi	_SFR_IO_ADDR(PORTB), 6
    rcall comm_rx_byte
    cpi	temp, 0x31
    breq jump_auth1
    cpi	temp, 0x32
    breq jump_auth2
    cpi	temp, 0x33
    breq jump_auth_write
    cpi	temp, 0x34
    breq cmd_update_sn
    cpi	temp, 0x35
    breq cmd_write_nvram
    cpi	temp, 0x36
    breq cmd_read_nvram
    cbi	_SFR_IO_ADDR(PORTB), 6
    rjmp idle_wait

jump_auth1:
    rjmp cmd_auth_step_1
jump_auth2:
    rjmp cmd_auth_step_2
jump_auth_write:
    rjmp cmd_auth_write

/* NVRAM Access Commands */
cmd_write_nvram:
    rcall comm_rx_byte
    cpi	temp, 0x20
    brmi cmd_nvram_exit
    cpi	temp, 0x40
    brcc cmd_nvram_exit
    out	_SFR_IO_ADDR(EEAR), temp
    rcall comm_rx_byte
    out	_SFR_IO_ADDR(EEDR), temp
    sbi	_SFR_IO_ADDR(EECR), 1
cmd_nvram_exit:
    rcall comm_delay
    cbi	_SFR_IO_ADDR(PORTB), 6
    rjmp idle_wait

cmd_read_nvram:
    rcall comm_rx_byte
    cpi	temp, 0x20
    brmi cmd_nvram_exit
    cpi	temp, 0x40
    brcc cmd_nvram_exit
    rcall comm_delay
    cbi	_SFR_IO_ADDR(PORTB), 6
    out	_SFR_IO_ADDR(EEAR), temp
    sbi	_SFR_IO_ADDR(EECR), 0
    in	temp, _SFR_IO_ADDR(EEDR)
    rcall comm_delay
    rcall comm_tx_start
    rjmp comm_tx_byte_and_exit

/* Serial Number Update */
cmd_update_sn:
    rcall comm_rx_byte
    mov	s0, temp
    rcall comm_rx_byte
    mov	s1, temp
    rcall comm_rx_byte
    mov	s2, temp
    rcall comm_rx_byte
    mov	s3, temp
    rcall comm_delay
    cbi	_SFR_IO_ADDR(PORTB), 6
    mov	temp, zero
    cpi	temp, 0x00
    brne auth1_init_state
    ldi	temp, 0x02
    rcall eeprom_read_next
    in	sn0, _SFR_IO_ADDR(EEDR)
    rcall eeprom_read_next
    in	sn1, _SFR_IO_ADDR(EEDR)
    rcall eeprom_read_next
    in	sn2, _SFR_IO_ADDR(EEDR)
    rcall eeprom_read_next
    in	sn3, _SFR_IO_ADDR(EEDR)
    inc	temp
    rcall eeprom_read_next
    in	bsn0, _SFR_IO_ADDR(EEDR)
    rcall eeprom_read_next
    in	bsn1, _SFR_IO_ADDR(EEDR)
    rcall eeprom_read_next
    in	bsn2, _SFR_IO_ADDR(EEDR)
    rcall eeprom_read_next
    in	bsn3, _SFR_IO_ADDR(EEDR)
    cp	bsn0, sn0
    brmi update_sn_backup
    cp	bsn1, sn1
    brmi update_sn_backup
    cp	bsn2, sn2
    brmi update_sn_backup
    cp	temp, sn3
    brmi update_sn_backup
    rjmp auth1_init_state
update_sn_backup:
    ldi	temp, 0x07
    out	_SFR_IO_ADDR(EEDR), sn0
    rcall eeprom_write_wait_and_inc
    out	_SFR_IO_ADDR(EEDR), sn1
    rcall eeprom_write_wait_and_inc
    out	_SFR_IO_ADDR(EEDR), sn2
    rcall eeprom_write_wait_and_inc
    out	_SFR_IO_ADDR(EEDR), sn3
    rcall eeprom_write_wait_and_inc

/* Authentication Step 1 */
auth1_init_state:
    ldi	s4, CASE_ID_01
    ldi	s5, CASE_ID_23
    ldi	s6, 0x00
    ldi	s7, 0x00
    mov	s8, zero
    ldi	s9, 0x00
    ldi	s10, 0x00
    rjmp auth1_start
cmd_auth_step_1:
    rcall comm_rx_state
    rcall comm_delay
    cbi	_SFR_IO_ADDR(PORTB), 6
    ldi	s4, ZL_NUM_0
    ldi	s5, ZL_NUM_12
    ldi	s6, ZL_NUM_34
    ldi	s7, ZL_NUM_56
    ldi	s8, ZL_NUM_78
    ldi	s9, DATE_0
    ldi	s10, DATE_1
auth1_start:
    rcall crypto_apply_key_1
    ldi	temp, 0x1D
    eor	s5, temp
    ldi	temp, 0xE9
    eor	s6, temp
    ldi	temp, 0x43
    eor	s7, temp
    ldi	temp, 0x3F
    eor	s8, temp
    ldi	temp, 0xB8
    eor	s9, temp
    ldi	temp, 0x29
    eor	s10, temp
    ldi	temp, 0x32
    mov	loop_ext, temp
auth1_outer_loop:
    wdr
    rcall crypto_update_state
    mov	temp, s5
    rcall crypto_lcg_step_1
    mov	s5, res
    mov	temp, s6
    rcall crypto_lcg_step_1
    mov	s6, res
    mov	temp, s7
    rcall crypto_lcg_step_1
    mov	s7, res
    mov	temp, s8
    rcall crypto_lcg_step_1
    mov	s8, res
    mov	temp, s9
    rcall crypto_lcg_step_1
    mov	s9, res
    mov	temp, s10
    rcall crypto_lcg_step_1
    mov	s10, res
    ldi	temp, 0x03
    mov	loop_int, temp
auth1_rotate_loop:
    clc
    adc	s10, s10
    adc	s9, s9
    adc	s8, s8
    adc	s7, s7
    adc	s6, s6
    adc	s5, s5
    adc	s4, s4
    adc	s3, s3
    adc	s2, s2
    adc	s1, s1
    adc	s0, s0
    brcc auth1_rotate_done
    ori	s10, 0x01
auth1_rotate_done:
    dec	loop_int
    brne auth1_rotate_loop
    dec	loop_ext
    brne auth1_outer_loop
    rcall crypto_apply_key_2
    ldi	temp, 0x8E
    eor	s5, temp
    ldi	temp, 0x65
    eor	s6, temp
    ldi	temp, 0xE1
    eor	s7, temp
    ldi	temp, 0xA3
    eor	s8, temp
    ldi	temp, 0x74
    eor	s9, temp
    ldi	temp, 0x33
    eor	s10, temp
    wdr
    rcall comm_tx_start
    rcall comm_tx_state
    mov	temp, s5
    rcall comm_tx_byte
    mov	temp, s6
    rcall comm_tx_byte
    mov	temp, s7
    rcall comm_tx_byte
    mov	temp, s8
    rcall comm_tx_byte
    mov	temp, s9
    rcall comm_tx_byte
    mov	temp, s10
comm_tx_byte_and_exit:
    rcall comm_tx_byte
    cbi	_SFR_IO_ADDR(PORTB), 6
    rcall comm_delay
    rjmp idle_wait

/* Authentication Step 2 */
cmd_auth_step_2:
    rcall comm_rx_state
    rcall comm_rx_byte
    rcall comm_delay
    cbi	_SFR_IO_ADDR(PORTB), 6
    out	_SFR_IO_ADDR(EEAR), temp
    sbi	_SFR_IO_ADDR(EECR), 0
    in	s4, _SFR_IO_ADDR(EEDR)
    rcall crypto_apply_key_1
    ldi	temp, 0x32
    mov	loop_ext, temp
auth2_outer_loop:
    wdr
    rcall crypto_update_state
    ldi	temp, 0x03
    mov	loop_int, temp
auth2_rotate_loop:
    clc
    adc	s4, s4
    adc	s3, s3
    adc	s2, s2
    adc	s1, s1
    adc	s0, s0
    brcc auth2_rotate_done
    ori	s4, 0x01
auth2_rotate_done:
    dec	loop_int
    brne auth2_rotate_loop
    dec	loop_ext
    brne auth2_outer_loop
    rcall crypto_apply_key_2
    wdr
    rcall comm_tx_start
    rcall comm_tx_state
    rjmp comm_tx_byte_and_exit
    rcall comm_delay

/* Authenticated Write Command */
cmd_auth_write:
    rcall comm_delay
    cbi	_SFR_IO_ADDR(PORTB), 6
    rcall comm_delay
    wdr
    rcall comm_tx_start
    mov	temp, ent0
    rcall comm_tx_byte
    mov	temp, ent1
    rcall comm_tx_byte
    mov	temp, ent2
    rcall comm_tx_byte
    mov	temp, ent3
    rcall comm_tx_byte
    wdr
    cbi	_SFR_IO_ADDR(PORTB), 6
    rcall comm_delay
    ldi	cnt, 0x32
entropy_wait_loop:
    sbic	_SFR_IO_ADDR(PINB), 5
    rjmp entropy_received
    wdr
    rcall comm_delay
    dec	cnt
    brne entropy_wait_loop
    rjmp idle_wait
entropy_received:
    sbi	_SFR_IO_ADDR(PORTB), 6
    rcall comm_rx_state
    rcall comm_rx_byte
    mov	s4, temp
    rcall comm_rx_byte
    mov	s5, temp
    rcall comm_delay
    cbi	_SFR_IO_ADDR(PORTB), 6
    ldi	temp, 0x33
    eor	s0, temp
    ldi	temp, 0xFB
    eor	s1, temp
    ldi	temp, 0xC7
    eor	s2, temp
    ldi	temp, 0x52
    eor	s3, temp
    ldi	temp, 0xC9
    eor	s4, temp
    ldi	temp, 0x8E
    eor	s5, temp
    ldi	temp, 0x65
    ldi	temp, 0x32
    mov	loop_ext, temp
entropy_outer_loop:
    wdr
    ldi	temp, 0x03
    mov	loop_int, temp
entropy_rotate_loop:
    clc
    ror	s0
    ror	s1
    ror	s2
    ror	s3
    ror	s4
    ror	s5
    brcc entropy_rotate_done
    ori	s0, 0x80
entropy_rotate_done:
    dec	loop_int
    brne entropy_rotate_loop
    mov	temp, s0
    rcall crypto_lcg_step_2
    mov	s0, res
    mov	temp, s1
    rcall crypto_lcg_step_2
    mov	s1, res
    mov	temp, s2
    rcall crypto_lcg_step_2
    mov	s2, res
    mov	temp, s3
    rcall crypto_lcg_step_2
    mov	s3, res
    mov	temp, s4
    rcall crypto_lcg_step_2
    mov	s4, res
    mov	temp, s5
    rcall crypto_lcg_step_2
    mov	s5, res
    dec	loop_ext
    brne entropy_outer_loop
    ldi	temp, 0x29
    eor	s0, temp
    ldi	temp, 0x91
    eor	s1, temp
    ldi	temp, 0xA7
    eor	s2, temp
    ldi	temp, 0xF1
    eor	s3, temp
    ldi	temp, 0x6B
    eor	s4, temp
    ldi	temp, 0x1D
    eor	s5, temp
    ldi	temp, 0xE9
    wdr
    cp	ent0, s0
    brne cmd_auth_write_done
    cp	ent1, s1
    brne cmd_auth_write_done
    cp	ent2, s2
    brne cmd_auth_write_done
    cp	ent3, s3
    brne cmd_auth_write_done
    out	_SFR_IO_ADDR(EEDR), s5
    out	_SFR_IO_ADDR(EEAR), s4
    sbi	_SFR_IO_ADDR(EECR), 1
eeprom_write_final_wait:
    sbic	_SFR_IO_ADDR(EECR), 1
    rjmp eeprom_write_final_wait
cmd_auth_write_done:
    rjmp idle_wait
