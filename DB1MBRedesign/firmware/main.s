; MC68331CAG16

SCCR0	EQU	$fffffc08

	org	$fc0

	movea.w	#SCCR0,A0
	; sci baud clock rate = 16,78MHz / (32 * X)
	; 16,78MHz / (32 * 9) = 58264 Hz
	; 	close enough to		57600 bd
	move.w	#$9,(A0)+
	; A0 +2
	; SCCR1 enable TE and RE
	move.w	#$c,(A0)+
	; A0 +2 -> SCSR = status
	movea.w	A0,A1
	addq.w	#$2,A1
	; A1 +2 -> SCDR = data
	movea.w	#$400,A2
	; set target addr in A2
	clr.w	D0
	clr.w	D1
	move.w	#$bbf,D3
wait_for_rx_full:
	; test bit 6 RDRF — Receive Data Register Full
	btst.b	#$6,($1,A0)
	beq.b	wait_for_rx_full
	; move status into D0
	move.b	($1,A0),D0
	; bits 0-4 are parity,framing,noise,overrun errors
	andi.b	#$f,D0
	bne.w	onerror
	; move data from SCDR into 0x400 and then advance to the next addr
	move.b	($1,A1),(A2)+
	tst.w	D3
	dbeq	D3,wait_for_rx_full
onerror:
	; send error code back
	move.b	D0,($1,A1)
	; die
	db $4a
	db $fa
