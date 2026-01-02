"""
SerialLoader
- GUI: tkinter (Tcl/Tk)
- Serial: pyserial

Usage:
  python serial_loader.py

Requirements:
  pip install pyserial

"""
from __future__ import annotations
import threading
import time
import struct
import os
import sys
from typing import Optional, List
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, colorchooser
import serial
import serial.tools.list_ports
import queue

DEFAULT_HEX = "7c6b696c6cfdc4551b53594e4353594e4357414954474f0a"

class SerialLoaderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('SerialLoader')
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # State variables
        self.byte_2 = self.convert_hex_string_to_byte_array(DEFAULT_HEX)
        self.fileData: bytes = b''
        self.processedFileData: bytes = b''
        self.int_0 = 64
        self.int_1 = 0
        self.int_2 = 0
        self.schnelleDB = False
        self.magicNumber = 0
        self.bool_0 = False
        self.bool_1 = False
        self.bool_2 = False

        # Serial
        self.serial_port: Optional[serial.Serial] = None
        self.serial_lock = threading.Lock()
        self.rx_queue: queue.Queue = queue.Queue()
        self.stop_upload = threading.Event()

        # Build UI
        self.create_widgets()
        self.load_ports()

        # start periodic check for incoming serial data
        self.after(100, self.process_rx_queue)

    def create_widgets(self):
        frm_top = ttk.Frame(self)
        frm_top.pack(fill='x', padx=6, pady=6)

        # Ports
        ttk.Label(frm_top, text='Port').grid(row=0, column=0, sticky='w')
        self.port_var = tk.StringVar()
        self.combo_ports = ttk.Combobox(frm_top, textvariable=self.port_var, state='readonly', width=12)
        self.combo_ports.grid(row=0, column=1, padx=4)

        self.btn_connect = ttk.Button(frm_top, text='Verbinden', command=self.on_connect)
        self.btn_connect.grid(row=0, column=2, padx=4)

        # Function selection
        ttk.Label(frm_top, text='Funktion').grid(row=1, column=0, sticky='w')
        self.func_var = tk.StringVar()
        self.combo_func = ttk.Combobox(frm_top, textvariable=self.func_var, state='readonly', values=['Kill', 'Upload', 'Datum', 'Bytes'])
        self.combo_func.grid(row=1, column=1, padx=4)
        self.combo_func.current(2)

        self.btn_go = ttk.Button(frm_top, text='Los', command=self.on_go)
        self.btn_go.grid(row=1, column=2, padx=4)

        # File controls
        frm_file = ttk.LabelFrame(self, text='Loader')
        frm_file.pack(fill='x', padx=6, pady=(0,6))
        self.btn_open = ttk.Button(frm_file, text='Öffnen...', command=self.on_open)
        self.btn_open.pack(side='left', padx=4, pady=4)
        self.btn_upload = ttk.Button(frm_file, text='Upload', command=self.on_upload, state='disabled')
        self.btn_upload.pack(side='left', padx=4, pady=4)

        # Log
        frm_log = ttk.LabelFrame(self, text='Log')
        frm_log.pack(fill='both', expand=True, padx=6, pady=6)
        self.txt_log = tk.Text(frm_log, height=16, wrap='none', font=('Consolas',10))
        self.txt_log.pack(fill='both', expand=True)
        self.txt_log.insert('end','Port auswählen\nVerbinden\nLoader Öffnen...\nLoader Upload\nFunktion Datum Los\nFunktion Upload Los\nFertig :)\n')

        # Bottom panel: progress and abort
        frm_bottom = ttk.Frame(self)
        frm_bottom.pack(fill='x', padx=6, pady=(0,6))
        self.led = tk.Canvas(frm_bottom, width=14, height=14)
        self.led.create_rectangle(0,0,14,14, fill='red', tags=('led',))
        self.led.pack(side='left', padx=(0,8))

        self.progress = ttk.Progressbar(frm_bottom, orient='horizontal', mode='determinate')
        self.progress.pack(side='left', fill='x', expand=True)

        self.btn_abort = ttk.Button(frm_bottom, text='Abbrechen', command=self.on_abort)
        self.btn_abort.pack(side='right', padx=4)

        # Status bar
        self.status_var = tk.StringVar(value='Not connected')
        self.status = ttk.Label(self, textvariable=self.status_var, relief='sunken', anchor='w')
        self.status.pack(fill='x', side='bottom')

    def log(self, msg: str, color: Optional[str]=None):
        # color not applied (tk.Text color would require tags) - keep simple
        self.txt_log.insert('end', msg + '\n')
        self.txt_log.see('end')

    def load_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.combo_ports['values'] = ports
        if ports:
            self.combo_ports.current(0)
            self.bool_0 = True
            self.led.itemconfig('led', fill='darkgreen')
            self.btn_go['state'] = 'normal'
        else:
            self.log('Konnte keinen COM-Port finden!')
            self.btn_go['state'] = 'disabled'
            self.combo_ports['values'] = []

    def on_connect(self):
        try:
            if self.serial_port and self.serial_port.is_open:
                with self.serial_lock:
                    self.serial_port.close()
                self.serial_port = None
                self.btn_connect.config(text='Verbinden')
                self.combo_ports['state'] = 'readonly'
                self.status_var.set('Getrennt...')
                self.led.itemconfig('led', fill='red')
            else:
                port = self.port_var.get() or (self.combo_ports.get() if self.combo_ports.get() else None)
                if not port:
                    messagebox.showerror('Fehler','Kein Port ausgewählt')
                    return
                ser = serial.Serial(port=port, baudrate=57600, timeout=0.1, write_timeout=2.5)
                with self.serial_lock:
                    self.serial_port = ser
                # start reader thread
                threading.Thread(target=self.reader_thread, daemon=True).start()
                self.btn_connect.config(text='Trennen')
                self.combo_ports['state'] = 'disabled'
                self.status_var.set(f'Verbunden mit {port}')
                self.led.itemconfig('led', fill='darkgreen')
        except Exception as e:
            self.log(str(e))

    def reader_thread(self):
        # Read from serial and push to rx_queue
        try:
            while self.serial_port and self.serial_port.is_open:
                try:
                    data = self.serial_port.read(self.serial_port.in_waiting or 1)
                    if data:
                        self.rx_queue.put(data)
                    else:
                        time.sleep(0.05)
                except serial.SerialException:
                    break
        except Exception as e:
            self.log('Reader error: ' + str(e))

    def process_rx_queue(self):
        # Called in main thread periodically
        try:
            while not self.rx_queue.empty():
                data = self.rx_queue.get_nowait()
                self.handle_incoming(data)
        except queue.Empty:
            pass
        self.after(100, self.process_rx_queue)

    def handle_incoming(self, data: bytes):
        # if byte == 0x1B, show the hex of it and next byte
        if len(data) <= 1:
            return
        if data[0] == 0xFF:
            return
        responses = {
            0x31: "Unbekannter Befehl",
            0x32: "Warte auf weitere Daten.",
            0x33: "Datei OK, wird gestartet.",
            0x34: "Initialisierung der Daten abgeschlossen."
        }
        for i in range(len(data)-1):
            if data[i] == 0x1B:
                code = data[i+1]
                if code in responses:
                    msg = responses[code]
                    self.log(msg)
                    self.status_var.set(msg)
                else:
                    self.status_var.set(f"{data[i]:02X} {data[i+1]:02X}")
        # also log raw incoming as hex
        self.log('RX: ' + ' '.join(f"{b:02X}" for b in data))

    def on_go(self):
        idx = self.combo_func.current()
        if idx == 0:  # Kill
            if not (self.serial_port and self.serial_port.is_open):
                self.log('Nicht verbunden...!')
                return
            if messagebox.askokcancel('Hey', 'Bereit zum töten...?'):
                self.sender_method(0)
                self.log('Kugel abgefeuert...!')
            else:
                self.log('Gerettet :)')
        elif idx == 1:  # Upload
            self.sender_method(1)
        elif idx == 2:  # Datum
            self.sender_method(2)
        elif idx == 3:  # Bytes
            self.sender_method(3)
        else:
            self.log('Unbekannte Funktion')

    def on_open(self):
        self.load_file(dialog=True)

    def on_upload(self):
        if not (self.serial_port and self.serial_port.is_open):
            self.log('Nicht verbunden...!')
            return
        # start background upload thread
        total = len(self.fileData) if not self.bool_2 else len(self.processedFileData)
        self.progress['maximum'] = max(1, total)
        self.stop_upload.clear()
        threading.Thread(target=self.upload_thread, daemon=True).start()

    def on_abort(self):
        self.stop_upload.set()
        self.bool_1 = True

    def sender_method(self, mode: int):
        if not (self.serial_port and self.serial_port.is_open):
            self.log('Nicht verbunden...!')
            return
        try:
            buffer = b''
            if mode == 0:
                buffer = bytes(self.byte_2[:8])
            elif mode == 1:
                # Upload special sequence: set bool_2 and load processed file
                self.bool_2 = True
                ok = self.load_file(dialog=True)
                if not ok:
                    self.log('Abbruch...!')
                    self.bool_2 = False
                    return
                # construct 24-byte header from byte_2[8:24]
                head = bytes(self.byte_2[8:8+16])
                # pad to 24 bytes
                buffer = head + bytes(8)
            elif mode == 2:
                # Datum
                now = time.localtime()
                weekday = now.tm_wday + 1  # Monday=1 in C# DayOfWeek mapping originally
                # Python tm_wday: Monday=0..Sunday=6 -> map +1
                Header1 = weekday
                Header2 = 0 if time.localtime().tm_isdst else 1
                # Ask user whether to use custom year (simulate YearForm radio)
                use_custom = messagebox.askyesno('Jahreszahl', 'Eigenes Jahr setzen?')
                if use_custom:
                    year = simpledialog.askinteger('Jahreszahl', 'Letzten 2 Ziffern des Jahres (z.B. 25):', minvalue=0, maxvalue=99)
                    if year is None:
                        self.log('Abbruch...!')
                        return
                    yyyy = year
                else:
                    yyyy = now.tm_year % 100

                numArray = bytearray(24)
                # first 16 bytes from byte_2[8:24]
                numArray[0:16] = self.byte_2[8:8+16]
                numArray[16] = self.shiftmod(now.tm_hour)
                numArray[17] = self.shiftmod(now.tm_min)
                numArray[18] = Header2
                numArray[19] = self.shiftmod(now.tm_mday)
                numArray[20] = self.shiftmod(now.tm_mon)
                numArray[21] = self.shiftmod(yyyy)
                numArray[22] = Header1
                # checksum: sum bytes from index 16 to len-2
                s = 0
                for i in range(16, len(numArray)-1):
                    s = (s + numArray[i]) & 0xFF
                numArray[-1] = s
                buffer = bytes(numArray)
                self.log('Parameter wurden gesendet...!')
            elif mode == 3:
                # Bytes: ask user for hex input
                s = simpledialog.askstring('Bytes', 'Hex Bytes eingeben (z.B. 1A 2B)')
                if not s:
                    return
                parts = [p.strip() for p in s.replace(',', ' ').split() if p.strip()]
                try:
                    b_list = bytes(int(x,16) for x in parts)
                    buffer = b_list
                except Exception as e:
                    self.log(str(e))
                    return
                # log sent hex
                self.log('TX: ' + ', '.join(f"{b:02X}" for b in buffer))
                self.status_var.set('Byte(s) wurden gesendet...!')

            # write buffer byte by byte with small delay
            for b in buffer:
                with self.serial_lock:
                    if self.serial_port and self.serial_port.is_open:
                        self.serial_port.write(bytes([b]))
                time.sleep(0.002)

            if self.bool_2:
                # prepare progress and start background upload
                total = len(self.processedFileData)
                self.progress['maximum'] = max(1, total)
                self.stop_upload.clear()
                threading.Thread(target=self.upload_thread, daemon=True).start()

        except Exception as e:
            self.log(str(e))

    def load_file(self, dialog: bool=True) -> bool:
        try:
            if not dialog:
                return False
            path = filedialog.askopenfilename()
            if not path:
                return False
            size = os.path.getsize(path)
            if 256 <= size <= 4*1024*1024:
                if not self.bool_2:
                    self.fileData = open(path,'rb').read()
                    self.int_1 = len(self.fileData) % self.int_0
                    self.status_var.set('Loader ' + os.path.basename(path))
                    self.btn_upload['state'] = 'normal'
                    self.log(f"Datei '{os.path.basename(path)}', Länge (0x{len(self.fileData):X}) {len(self.fileData)} Bytes geladen...!")
                    return True
                else:
                    self.processedFileData = open(path,'rb').read()
                    self.int_2 = len(self.processedFileData) % self.int_0
                    header1 = self.swap_reverse(self.processedFileData, 4)
                    header2 = self.swap_reverse(self.processedFileData, 8)
                    if (header1 ^ header2) == 0xFFFFFFFF and (header1 - 4096) == (size - 1):
                        self.log(f"Binärdatei '{os.path.basename(path)}', Länge (0x{len(self.processedFileData):X}) {len(self.processedFileData)} Bytes geladen...!")
                        self.magicNumber = self.swap_reverse(self.processedFileData, 12)
                        # check magic numbers roughly as original
                        mag = self.magicNumber
                        groupA = {826366210, 826366246, 1633972226, 1633972227}
                        groupB = {1633944322,1633944579,1633944580,1633944836,1633945092}
                        if mag in groupA:
                            self.schnelleDB = False
                            self.status_var.set('\nTyp A')
                        elif mag in groupB:
                            self.schnelleDB = True
                            self.status_var.set('\nTyp B')
                        else:
                            self.schnelleDB = False
                            self.status_var.set('\nTyp unbekannt')
                        self.btn_upload['state'] = 'normal'
                        return True
                    else:
                        self.log('Header kaputt oder falscher Dateityp...!')
            else:
                self.log('Fehler, falsche Größe oder kaputt...!')
                self.btn_upload['state'] = 'disabled'
        except Exception as e:
            self.log(str(e))
        return False

    def upload_thread(self):
        try:
            with self.serial_lock:
                if not (self.serial_port and self.serial_port.is_open):
                    self.log('Nicht verbunden...!')
                    return
                # discard out buffer not directly available; flush output
                try:
                    self.serial_port.reset_output_buffer()
                except Exception:
                    pass

            if self.bool_2:
                # first 256 bytes
                data = self.processedFileData
                # send first 256 bytes one by one
                for i in range(256):
                    if self.stop_upload.is_set():
                        self.log('Upload abgebrochen...!')
                        return
                    with self.serial_lock:
                        self.serial_port.write(bytes([data[i]]))
                    self.progress['value'] = i
                time.sleep(0.025)
                if self.schnelleDB:
                    # reopen at 115200
                    with self.serial_lock:
                        self.serial_port.baudrate = 115200
                        # depending on implementation, need to reopen - pyserial allows changing baudrate
                num = 256
                while num < len(data) - self.int_2:
                    if self.stop_upload.is_set():
                        self.log('Upload abgebrochen...!')
                        return
                    with self.serial_lock:
                        self.serial_port.write(data[num:num+self.int_0])
                    self.progress['value'] = num
                    num += self.int_0
                # final remainder
                with self.serial_lock:
                    self.serial_port.write(data[num:num+self.int_2])
                self.progress['value'] = num + self.int_2
            else:
                data = self.fileData
                num = 0
                while num < len(data) - self.int_1:
                    if self.stop_upload.is_set():
                        self.log('Upload abgebrochen...!')
                        return
                    with self.serial_lock:
                        self.serial_port.write(data[num:num+self.int_0])
                    self.progress['value'] = num
                    num += self.int_0
                with self.serial_lock:
                    self.serial_port.write(data[num:num+self.int_1])
                self.progress['value'] = num + self.int_1

            # finish
            if self.bool_2:
                self.log('Upload fertig...!')
                # restore baudrate to 57600 if we changed it
                with self.serial_lock:
                    try:
                        self.serial_port.baudrate = 57600
                    except Exception:
                        pass
                self.bool_2 = False
            else:
                self.log('Upload fertig...!')
        except Exception as e:
            self.log('Upload Fehler: ' + str(e))
        finally:
            # reset abort flag
            self.bool_1 = False

    # Helper functions
    def convert_hex_string_to_byte_array(self, hex_string: str) -> bytes:
        if len(hex_string) % 2 != 0:
            raise ValueError(f"Der Binärschlüssel muss gerade sein: {hex_string}")
        return bytes(int(hex_string[i:i+2],16) for i in range(0,len(hex_string),2))

    def shiftmod(self, v: int) -> int:
        # uint_1/10 <<4 | uint_1%10
        return ((v // 10) << 4) | (v % 10)

    def swap_reverse(self, data: bytes, offset: int) -> int:
        # copy 4 bytes, reverse, return unsigned int
        chunk = bytearray(data[offset:offset+4])
        chunk.reverse()
        return struct.unpack('<I', bytes(chunk))[0]

    def on_close(self):
        try:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
        except Exception:
            pass
        self.destroy()

if __name__ == '__main__':
    try:
        app = SerialLoaderApp()
        app.mainloop()
    except Exception as e:
        print('Fatal:', e)
