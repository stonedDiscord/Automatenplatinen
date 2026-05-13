| MC68331CAG16
| Based on CPU32 instruction set

    .section .text

SCCR0 = 0xfffffc08

    .org 0xfc0

    moveaw #SCCR0, %a0
    | sci baud clock rate = 16,78MHz / (32 * X)
    | 16,78MHz / (32 * 9) = 58264 Hz
    |      close enough to          57600 bd
    movew #0x9, (%a0)+
    | A0 +2
    | SCCR1 enable TE and RE
    movew #0xc, (%a0)+
    | A0 +2 -> SCSR = status
    moveaw %a0, %a1
    addqw #0x2, %a1
    | A1 +2 -> SCDR = data
    moveaw #0x400, %a2
    | set target addr in A2
    clrw %d0
    clrw %d1
    movew #0xbbf, %d3
wait_for_rx_full:
    | test bit 6 RDRF — Receive Data Register Full
    btstb #0x6, 1(%a0)
    beq.b wait_for_rx_full
    | move status into D0
    moveb 1(%a0), %d0
    | bits 0-4 are parity,framing,noise,overrun errors
    andib #0xf, %d0
    bne.w onfinish
    | move data from SCDR into 0x400 and then advance to the next addr
    moveb 1(%a1), (%a2)+
    tstw %d3
    dbeq %d3, wait_for_rx_full
onfinish:
    | reset serial
    moveb %d0, 1(%a1)
    | hand back control
    bgnd
