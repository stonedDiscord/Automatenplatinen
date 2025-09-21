#!/usr/bin/env python3
"""
patcher3.py - Reimplementation of the PureBasic EPROM patcher in Python using Tkinter.
"""

import os
import hashlib
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

romBuffer = bytearray()
romSize = 0
loaded_dual = False
odd_path = ""
even_path = ""
single_path = ""

StatusBarText = None
ProgressBar = None

current_patch_bytes = b""
PATCH_DATA_CHECKSUM_PATTERN = b"\xb0\x90\x67\x0e"
PATCH_DATA_CHECKSUM_VALUE =   b"\x20\x10\x60\x0e"

PATCH_DATA_DATE_PATTERN = b"\x70\x02\x2f\x00\x70\x10\x2f\x00\x4e\xb9\x00\x00"
PATCH_DATA_DATE_VALUE =   b"\x70\x02\x2F\x00\x70\x10\x2F\x00\x4E\xB9\x00\x0F\xFF\x04"

PATCH_DATA_ZULASSUNG_PATTERN = b"\x2f\x0a\x70\x01\x2f\x00\x70\x10\x2f\x00\x4e\xb9\x00\x00"
PATCH_DATA_ZULASSUNG_VALUE =   b"\x2F\x0A\x70\x01\x2F\x00\x70\x10\x2F\x00\x4E\xB9\x00\x0F\xFF\x0C"

PATCH_DATA_INITRAM1_PATTERN = b"\x4f\xef\x00\x0c\x36\xbc\x00\x01"
PATCH_DATA_INITRAM1_VALUE =   b"\x4f\xef\x00\x0c\x36\xbc\x00\x02"

PATCH_DATA_INITRAM2_PATTERN = b"\x4f\xef\x00\x0c\x36\xbc\x00\x01"
PATCH_DATA_INITRAM2_VALUE =   b"\x4f\xef\x00\x0c\x36\xbc\x00\x02"

PATCH_DATA_DATUM_UHR_PATTERN = b"DATUM - UHR    "

PATCH_DATA_FIXED = b"\x31\x12\x10\x00\x20\x3c\x00\x0f\xff\x00\x4e\x75\x30\x2f\x00\x06\x22\x2f\x00\x08\x4e\x4d\x4e\x71\x0c\x80\x12\x34\x56\x78\x67\x06\x06\x80\x00\xa9\x8a\xc7\x4e\x75"  # DAT_0040a4d8 (40 bytes)

def convert_date(date_str):
    try:
        if len(date_str) == 8:
            year = int(date_str[0:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])
            # Convert to BCD
            def to_bcd(n):
                return ((n // 10) << 4) | (n % 10)
            return bytes([to_bcd(day), to_bcd(month), to_bcd(year % 100), 0])
    except ValueError:
        pass
    return b'\x00\x00\x00\x00'

def set_status(text: str):
    if StatusBarText:
        StatusBarText.config(text=text)
        StatusBarText.update_idletasks()
    if not text.startswith("Suche") and not text.startswith("Muster gefunden"):
        print(f"[STATUS] {text}")

def update_progress(value: int):
    if ProgressBar:
        ProgressBar['value'] = max(0, min(100, value))
        ProgressBar.update_idletasks()

def byte_swap():
    if not romBuffer:
        return
    set_status("Byte-Paare tauschen...")
    last_progress = -1
    for i in range(0, len(romBuffer) - 1, 2):
        romBuffer[i], romBuffer[i + 1] = romBuffer[i + 1], romBuffer[i]
        prog = int((i / len(romBuffer)) * 100)
        if prog != last_progress:
            update_progress(prog)
            last_progress = prog
    set_status("Byte-Tausch abgeschlossen")
    update_progress(0)

def load_16bit_file():
    path = filedialog.askopenfilename(title="16-Bit-EPROM-Datei laden", filetypes=[("BIN-Dateien", "*.bin"), ("Alle Dateien", "*.*")])
    if not path:
        return False
    try:
        with open(path, "rb") as f:
            data = f.read()
        global romBuffer, romSize, single_path, loaded_dual
        romBuffer = bytearray(data)
        romSize = len(romBuffer)
        single_path = path
        loaded_dual = False
        set_status(f"16-Bit-ROM geladen: {os.path.basename(path)} ({romSize} bytes)")
        if romSize > 6 and romBuffer[6] == 0xfc:
            byte_swap()
        return True
    except Exception as e:
        messagebox.showerror("Fehler", f"Datei kann nicht geladen werden: {e}")
        return False

def load_dual_8bit_files():
    p1 = filedialog.askopenfilename(title="Erste 8-Bit-EPROM-Datei laden", filetypes=[("EPROM-Dateien", ("*.bin","*.ic10")), ("Alle Dateien", "*.*")])
    if not p1:
        return False
    p2 = filedialog.askopenfilename(title="Zweite 8-Bit-EPROM-Datei laden", filetypes=[("EPROM-Dateien", ("*.bin","*.ic14")), ("Alle Dateien", "*.*")])
    if not p2:
        return False
    try:
        with open(p1, "rb") as f1:
            odd = f1.read()
        with open(p2, "rb") as f2:
            even = f2.read()
        if len(odd) != len(even):
            messagebox.showwarning("Warnung", "ODD- und EVEN-Dateigrößen unterscheiden sich; mit minimaler Länge fortfahren.")
        L = min(len(odd), len(even))
        combined = bytearray()
        for i in range(L):
            combined.append(odd[i])
            combined.append(even[i])
        global romBuffer, romSize, loaded_dual, odd_path, even_path
        romBuffer = combined
        romSize = len(combined)
        loaded_dual = True
        odd_path = p1
        even_path = p2
        set_status(f"Duale 8-Bit geladen -> kombiniert ({romSize} bytes)")
        if romSize > 6 and romBuffer[6] == 0xfc:
            byte_swap()
        return True
    except Exception as e:
        messagebox.showerror("Fehler", f"Duale Dateien können nicht geladen werden: {e}")
        return False

def search_pattern(pattern: bytes) -> int:
    if not romBuffer or len(pattern) == 0 or len(pattern) >= 0x32:
        return -1
    plen = len(pattern)
    last_progress = -1
    for i in range(0, romSize - plen + 1, 2):
        prog = int((i / romSize) * 100)
        if prog != last_progress:
            update_progress(prog)
            set_status(f"Suche... {prog}%")
            last_progress = prog
        if romBuffer[i:i + plen] == pattern:
            set_status(f"Muster gefunden bei 0x{i:06X}")
            return i
    set_status("Muster nicht gefunden")
    update_progress(0)
    return -1

def apply_patch(offset: int, length: int):
    global romSize
    global current_patch_bytes
    if length <= 0 or length >= 0x32 or not current_patch_bytes:
        messagebox.showerror("Fehler", "Ungültige Patch-Länge oder keine Patch-Daten")
        return
    if offset + length > romSize:
        romBuffer.extend(b'\x00' * (offset + length - romSize))
        romSize = len(romBuffer)
    src = current_patch_bytes
    if len(src) < length:
        src += b'\x00' * (length - len(src))
    romBuffer[offset:offset + length] = src[:length]

def patch_eprom_data(date_str: str, zl_str: str) -> bool:
    global current_patch_bytes
    if not romBuffer:
        messagebox.showerror("Fehler", "Keine ROM geladen")
        return False

    set_status("Patch-Prozess starten...")
    update_progress(5)

    # Checksum patch
    current_patch_bytes = PATCH_DATA_CHECKSUM_PATTERN
    addr = search_pattern(current_patch_bytes)
    if addr == -1:
        messagebox.showwarning("Info", "Kann Checksumme nicht Patchen!")
    else:
        current_patch_bytes = PATCH_DATA_CHECKSUM_VALUE
        apply_patch(addr, 4)
        set_status(f"Checksumme lautet: ${addr:04X}\nWert: {current_patch_bytes.hex()}")
        update_progress(20)

    # Date/ID patch
    current_patch_bytes = PATCH_DATA_DATE_PATTERN
    addr = search_pattern(current_patch_bytes)
    if addr == -1:
        messagebox.showwarning("Info", "Kann Datum ID-Chip nicht Patchen!")
    else:
        # Use byte-swapped pattern + converted date (reimplements FUN_00401c7a logic)
        converted_date = convert_date(date_str)
        current_patch_bytes = PATCH_DATA_DATE_VALUE
        apply_patch(addr, 14)
        set_status(f"PatchDatum lautet: ${addr:04X}\nWert: {current_patch_bytes.hex()}")
        update_progress(40)

    # Zulassung patch
    current_patch_bytes = PATCH_DATA_ZULASSUNG_PATTERN
    addr = search_pattern(current_patch_bytes)
    if addr == -1:
        messagebox.showwarning("Info", "Kann Zulassung ID-Chip nicht Patchen!")
    else:
        current_patch_bytes = PATCH_DATA_ZULASSUNG_VALUE
        apply_patch(addr, 16)
        set_status(f"Zulassung lautet: ${addr:04X}\nWert: {current_patch_bytes.hex()}")
        update_progress(60)

    # Init RAM patch (try pattern 1, fallback to 2)
    current_patch_bytes = PATCH_DATA_INITRAM1_PATTERN
    addr = search_pattern(current_patch_bytes)
    if addr != -1:
        current_patch_bytes = PATCH_DATA_INITRAM1_VALUE
        apply_patch(addr, 8)
        set_status(f"PatchInitRam 1 lautet: ${addr:04X}\nWert: {current_patch_bytes.hex()}")
    else:
        current_patch_bytes = PATCH_DATA_INITRAM2_PATTERN
        addr = search_pattern(current_patch_bytes)
        if addr != -1:
            current_patch_bytes = PATCH_DATA_INITRAM2_VALUE
            apply_patch(addr, 8)
            set_status(f"PatchInitRam 2 lautet: ${addr:04X}\nWert: {current_patch_bytes.hex()}")
        else:
            messagebox.showwarning("Info", "Kann Init-Ram Typ1 u. 2 nicht Patchen!")
    update_progress(75)

    # Date/Time patch
    current_patch_bytes = PATCH_DATA_DATUM_UHR_PATTERN
    addr = search_pattern(current_patch_bytes)
    if addr == -1:
        messagebox.showwarning("Info", "Kann DATUM - UHR Teil1 nicht finden !")
    else:
        # Find second occurrence or something (emulate SearchAddress)
        # Placeholder: write at addr + 0x0E
        current_patch_bytes = b"\x20"
        apply_patch(addr + len(PATCH_DATA_DATUM_UHR_PATTERN), 1)
        set_status(f"DatumUhr 1 lautet: ${addr:04X}\nWert: {current_patch_bytes.hex()}")
    
    update_progress(80)
    
    addr = search_pattern(addr.to_bytes(4, byteorder = 'big'))
    if addr == -1:
        messagebox.showwarning("Info", f"Kann DATUM - UHR Teil2 nicht finden !\nWert: {addr.to_bytes(4, byteorder = 'big')}")
    else:
        current_patch_bytes = b"\x00\x00"
        apply_patch(addr + 0x0E, 2)
        set_status(f"DatumUhr 2 lautet: ${addr + 0x0E:04X}\nWert: {current_patch_bytes.hex()}")

    update_progress(90)

    # Fixed block at 0xFFF00
    fixed_addr = 0xFFF00
    if romSize > fixed_addr:
        current_patch_bytes = PATCH_DATA_FIXED
        apply_patch(fixed_addr, 0x28)

        # Apply date conversion to fixed block
        converted = convert_date(date_str)
        romBuffer[fixed_addr:fixed_addr+4] = converted
        set_status(f"Fester Block gepatcht bei 0x{fixed_addr:06X}")

        # Apply zl nummer
        converted = int(zl_str).to_bytes(4, byteorder = 'big')
        romBuffer[fixed_addr+26:fixed_addr+30] = converted
        messagebox.showinfo("Info", f"Fester Block gepatcht bei 0x{fixed_addr+26:06X}\nWert: {converted}")
    else:
        set_status("ROM zu klein für festen Block")

    # Validate (placeholder)
    md5 = hashlib.md5(bytes(romBuffer)).hexdigest()
    set_status(f"Patchen abgeschlossen. MD5: {md5}")
    update_progress(100)

    # Export
    export_patched()
    return True

def export_patched():
    if not romBuffer:
        return
    if loaded_dual:
        odd = romBuffer[0::2]
        even = romBuffer[1::2]
        odd_out = os.path.splitext(odd_path)[0] + "_patched.ic10"
        even_out = os.path.splitext(even_path)[0] + "_patched.ic14"
        with open(odd_out, "wb") as f:
            f.write(odd)
        with open(even_out, "wb") as f:
            f.write(even)
        messagebox.showinfo("Exportieren", f"Gepatchte Dateien gespeichert:\n{odd_out}\n{even_out}")
    else:
        out = os.path.splitext(single_path)[0] + "_patched.bin"
        with open(out, "wb") as f:
            f.write(romBuffer)
        messagebox.showinfo("Exportieren", f"Gepatchte Datei gespeichert: {out}")

class App:
    def __init__(self, root):
        global StatusBarText, ProgressBar
        self.root = root
        root.title("EPROM Patcher v3")
        root.geometry("600x400")

        main = ttk.Frame(root, padding=10)
        main.pack(fill='both', expand=True)

        ttk.Button(main, text="16-Bit-Datei laden", command=load_16bit_file).pack(pady=5)
        ttk.Button(main, text="Duale 8-Bit-Dateien laden", command=load_dual_8bit_files).pack(pady=5)

        ttk.Label(main, text="Datum (JJJJMMTT):").pack()
        self.date_entry = ttk.Entry(main)
        self.date_entry.pack(fill='x', pady=5)
        self.date_entry.insert(0, datetime.now().strftime("%Y%m%d"))

        ttk.Label(main, text="Zulassungsnummer:").pack()
        self.zl_entry = ttk.Entry(main)
        self.zl_entry.pack(fill='x', pady=5)
        self.zl_entry.insert(0, "123456789")

        ttk.Button(main, text="ROM patchen", command=self.do_patch).pack(pady=10)

        ProgressBar = ttk.Progressbar(main, orient='horizontal', mode='determinate', maximum=100)
        ProgressBar.pack(fill='x', pady=5)

        StatusBarText = ttk.Label(root, text="Bereit", relief='sunken', anchor='w')
        StatusBarText.pack(side='bottom', fill='x')

    def do_patch(self):
        date = self.date_entry.get().strip()
        zl = self.zl_entry.get().strip()
        patch_eprom_data(date, zl)

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
