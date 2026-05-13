#!/bin/bash
m68k-elf-as -mcpu=cpu32 main.s -o main.o
m68k-elf-objcopy -O binary main.o init_raw.bin
dd if=init_raw.bin of=init.bin bs=1 skip=4032
rm main.o init_raw.bin
