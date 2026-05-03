#!/usr/bin/env bash
set -euo pipefail

ELF=".pio/build/ATmega48P/firmware.elf"
OUT="main_compiled.txt"

pio run

avr-objdump -d -j .text "$ELF" > "$OUT"

echo "Exported .text section assembly to $OUT"
