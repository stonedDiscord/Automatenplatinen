import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("PySerial nicht gefunden. Versuche Installation...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyserial"])
    import serial
    import serial.tools.list_ports

# ANSI color codes
RESET = "\033[0m"
RED_TEXT = "\033[41;97m"
YELLOW_TEXT = "\033[43;30m"
GREEN_TEXT = "\033[42;97m"


# Constants
V2_MACHINES = {
    "ADP 1002 (NEW STAR JP)": bytearray([6, 50, 2, 135]),
    "ADP 1002 (NEW STAR)": bytearray([6, 50, 2, 135]),
    "ADP 1003 (GOOD LUCK)": bytearray([6, 50, 2, 101]),
    "ADP 1005 (CONFETTI)": bytearray([6, 50, 129, 144]),
    "ADP 1005 (FILOU)": bytearray([6, 50, 129, 25]),
    "ADP 1005 (MEGA WINNER)": bytearray([6, 50, 129, 25]),
    "ADP 1006 (FIRST PARTY)": bytearray([6, 50, 146, 25]),
    "ADP 1006 (FUN BOX)": bytearray([6, 50, 146, 25]),
    "ADP 1010 (LOADED)": bytearray([6, 50, 2, 131]),
    "ADP 1012 (TRIO STANDGERÄT)": bytearray([6, 50, 129, 33]),
    "ADP 1017 (MULTI MULTI ERGOLINE)": bytearray([6, 50, 2, 145]),
    "ADP 1020 (WAIKIKI)": bytearray([6, 50, 146, 32]),
    "ADP 1020 (DRIBBLER)": bytearray([6, 50, 146, 32]),
    "ADP 1038 (MULTI MULTI STAND)": bytearray([6, 50, 2, 146]),
    "ADP 1181 (TALER GASTRO) CC3": bytearray([6, 50, 146, 51]),
    "ADP 1187 (HOT FIVE)": bytearray([6, 50, 129, 105]),
    "ADP 1222 (20 SPIELE)": bytearray([6, 50, 130, 2]),
    "ADP 1223 (LOKAL RUNDE)": bytearray([6, 50, 146, 86]),
    "ADP 1230 (SERIEN POWER) CC3": bytearray([6, 50, 146, 87]),
    "ADP 1243 (CRISS CROSS CAFE)": bytearray([6, 50, 146, 81]),
    "ADP 1081 BLUE DIAMOND": bytearray([6, 50, 3, 96]),
    "ALEX (BERLIN)": bytearray([6, 50, 146, 24]),
    "ADDERS&LADDERS": bytearray([6, 50, 1, 50]),
    "ALEX": bytearray([6, 50, 146, 24]),
    "ANNO TOBAK G EC1": bytearray([6, 50, 0, 132]),
    "AVANTI": bytearray([6, 50, 129, 6]),
    "BLUE BALL": bytearray([6, 50, 128, 72]),
    "BLUE POWER": bytearray([6, 50, 128, 148]),
    "BOBBY": bytearray([6, 50, 1, 73]),
    "BRAVO": bytearray([6, 50, 128, 5]),
    "BREAK OUT": bytearray([6, 50, 2, 89]),
    "BRILLANT": bytearray([6, 50, 1, 118]),
    "BRISANT": bytearray([6, 50, 128, 1]),
    "BUNGEE": bytearray([6, 50, 128, 33]),
    "CAIRO 150": bytearray([6, 50, 128, 133]),
    "CASHFUN": bytearray([6, 50, 2, 24]),
    "CARIBIC C1": bytearray([6, 50, 128, 105]),
    "CASTELL": bytearray([6, 50, 0, 2]),
    "CHILI": bytearray([6, 50, 128, 113]),
    "CINEMA": bytearray([6, 50, 128, 152]),
    "COCKTAILS": bytearray([6, 50, 2, 89]),
    "CRISS CROSS (TWENTY SEVEN)": bytearray([6, 50, 129, 9]),
    "CRISS CROSS": bytearray([6, 50, 129, 9]),
    "CROWN JEWELS CC3": bytearray([6, 50, 2, 81]),
    "CRUISER": bytearray([6, 50, 146, 23]),
    "DIEGO": bytearray([6, 50, 1, 133]),
    "DUBLIN": bytearray([6, 50, 128, 153]),
    "DYNASTY": bytearray([6, 50, 128, 67]),
    "EGYPT FUN": bytearray([6, 50, 2, 35]),
    "ESPRIT VIDEO": bytearray([6, 50, 146, 9]),
    "FOCUS EC1": bytearray([6, 50, 0, 80]),
    "FUN CITY PAS": bytearray([6, 50, 52, 65]),
    "FUN CITY PRO": bytearray([6, 50, 54, 4]),
    "FUN MASTER": bytearray([6, 50, 53, 134]),
    "GARANT G": bytearray([6, 50, 0, 129]),
    "GLUECKAUF": bytearray([6, 50, 1, 136]),
    "GOLD PLAY": bytearray([6, 50, 146, 19]),
    "GOLD PLAY DELUXE": bytearray([6, 50, 146, 19]),
    "GOLD STAR": bytearray([6, 50, 128, 66]),
    "GOOD LUCK": bytearray([6, 50, 146, 17]),
    "HAPPY": bytearray([6, 50, 0, 4]),
    "HIGHLIGHT WINNER": bytearray([6, 50, 0, 65]),
    "HOT CHERRY (LUCKY DAY)": bytearray([6, 50, 129, 24]),
    "HOT CHERRY": bytearray([6, 50, 129, 24]),
    "HOT DOG (NIGHT)": bytearray([6, 50, 129, 20]),
    "HOT DOG": bytearray([6, 50, 129, 20]),
    "HOT PEPPER": bytearray([6, 50, 129, 21]),
    "IMPULS 100": bytearray([6, 50, 146, 1]),
    "JAZZ": bytearray([6, 50, 129, 0]),
    "JOKER G": bytearray([6, 50, 0, 135]),
    "JOKER HERZ AS": bytearray([6, 50, 54, 20]),
    "KAISER BON BON": bytearray([6, 50, 146, 5]),
    "KAISER COOL": bytearray([6, 50, 146, 2]),
    "KAISER CROCO": bytearray([6, 50, 128, 147]),
    "KAISER MAGIER": bytearray([6, 50, 146, 0]),
    "LADY BLUE QUICK": bytearray([6, 50, 1, 57]),
    "LAOLA (FINALE 2010)": bytearray([6, 50, 146, 17]),
    "LAOLA": bytearray([6, 50, 146, 17]),
    "LOTUS": bytearray([6, 50, 2, 37]),
    "MEGA 199": bytearray([6, 50, 128, 69]),
    "MEGA AIR": bytearray([6, 50, 128, 112]),
    "MERKUR EURO CUP D12": bytearray([6, 50, 1, 117]),
    "MEGA DENVER": bytearray([6, 50, 128, 97]),
    "MEGA GHOST": bytearray([6, 50, 128, 121]),
    "MEGA MEXICO": bytearray([6, 50, 128, 131]),
    "MEGA PAN": bytearray([6, 50, 128, 102]),
    "MEGA ROAD": bytearray([6, 50, 128, 132]),
    "MEGA ZACK": bytearray([6, 50, 128, 99]),
    "MEGA LIFE": bytearray([6, 50, 128, 100]),
    "MEGA TURBO SUNNY": bytearray([6, 50, 128, 56]),
    "MEGA-X": bytearray([6, 50, 128, 54]),
    "MERKUR 2000": bytearray([6, 50, 0, 81]),
    "MERKUR 5000": bytearray([6, 50, 1, 23]),
    "MERKUR ALSUNA": bytearray([6, 50, 0, 137]),
    "MERKUR AZZURO": bytearray([6, 50, 1, 96]),
    "MERKUR BEAMER": bytearray([6, 50, 2, 53]),
    "MERKUR CASHFIRE": bytearray([6, 50, 2, 57]),
    "MERKUR CHARLY": bytearray([6, 50, 1, 53]),
    "MERKUR CRAZY MONEY": bytearray([6, 50, 41, 9]),
    "MERKUR DORO": bytearray([6, 50, 1, 84]),
    "MERKUR EURO CUP": bytearray([6, 50, 1, 117]),
    "MERKUR GOLDPOKAL": bytearray([6, 50, 1, 51]),
    "MERKUR GOLD CUP": bytearray([6, 50, 0, 149]),
    "MERKUR JACKPOT C J": bytearray([6, 50, 40, 5]),
    "MERKUR JACKPOT SL": bytearray([6, 50, 40, 5]),
    "MERKUR LASER": bytearray([6, 50, 2, 5]),
    "MERKUR LUCKY STAR": bytearray([6, 50, 2, 49]),
    "MERKUR MISTRAL": bytearray([6, 50, 1, 105]),
    "MERKUR MULTI CASINO": bytearray([6, 50, 2, 118]),
    "MERKUR MULTI ERGOLINE": bytearray([6, 50, 2, 116]),
    "MERKUR MULTI STAND": bytearray([6, 50, 2, 117]),
    "MERKUR ORCA": bytearray([6, 50, 1, 102]),
    "MERKUR RONDO": bytearray([6, 50, 1, 82]),
    "MERKUR RONDO N": bytearray([6, 50, 1, 82]),
    "MERKUR STAR": bytearray([6, 50, 2, 56]),
    "MERKUR STAR S": bytearray([6, 50, 2, 56]),
    "MERKUR STIXX": bytearray([6, 50, 1, 72]),
    "MERKUR STRATOS": bytearray([6, 50, 0, 116]),
    "MERKUR THUNDER": bytearray([6, 50, 1, 68]),
    "MERKUR TOP 180": bytearray([6, 50, 2, 2]),
    "MERKUR TORNADO": bytearray([6, 50, 1, 115]),
    "MERKUR TOWERS": bytearray([6, 50, 1, 86]),
    "MERKUR XXL": bytearray([6, 50, 1, 49]),
    "MERKUR XXL SUPER": bytearray([6, 50, 1, 69]),
    "MERKUR EUROSTAR": bytearray([6, 50, 0, 152]),
    "MIAMI": bytearray([6, 50, 128, 117]),
    "MOSQUITO": bytearray([6, 50, 2, 98]),
    "NEW WINNER (BIG JACKPOT)": bytearray([6, 50, 129, 5]),
    "NEW WINNER (EUROBANK)": bytearray([6, 50, 129, 5]),
    "NEW WINNER": bytearray([6, 50, 129, 5]),
    "NEXT GENERATION": bytearray([6, 50, 128, 80]),
    "OCEAN": bytearray([6, 50, 128, 135]),
    "OKTA": bytearray([6, 50, 128, 146]),
    "OLYMP": bytearray([6, 50, 128, 19]),
    "PALACE": bytearray([6, 50, 0, 69]),
    "PEPPER": bytearray([6, 50, 129, 2]),
    "PLAYERS INN": bytearray([6, 50, 128, 66]),
    "POKER POT": bytearray([6, 50, 98, 73]),
    "POKER STAR": bytearray([6, 50, 1, 97]),
    "POWER HERZ AS": bytearray([6, 50, 98, 119]),
    "PRIMA VERA G": bytearray([6, 50, 0, 121]),
    "QUICK BINGO D": bytearray([6, 50, 40, 83]),
    "RAINBOW": bytearray([6, 50, 1, 88]),
    "RAPTOR": bytearray([6, 50, 146, 21]),
    "RODEO G": bytearray([6, 50, 0, 148]),
    "RONDO STEP 1": bytearray([6, 50, 1, 134]),
    "RONDO STEP 2": bytearray([6, 50, 1, 150]),
    "SAM": bytearray([6, 50, 128, 65]),
    "SAPHIR G": bytearray([6, 50, 128, 49]),
    "SCIROCCO": bytearray([6, 50, 2, 25]),
    "SEKT ODER SELTERS": bytearray([6, 50, 53, 118]),
    "SHARK": bytearray([6, 50, 128, 89]),
    "SHOWDOWN": bytearray([6, 50, 128, 0]),
    "SIRIUS (GAMBLERS INN)": bytearray([6, 50, 129, 19]),
    "SIRIUS JACKPOT": bytearray([6, 50, 129, 18]),
    "SIRIUS JACKPOT EXT": bytearray([6, 50, 129, 18]),
    "SONNE": bytearray([6, 50, 128, 0]),
    "SONNENFREAKS": bytearray([6, 50, 0, 33]),
    "SONNENFUERST G": bytearray([6, 50, 0, 133]),
    "SPACE STAR": bytearray([6, 50, 0, 84]),
    "STRIKE": bytearray([6, 50, 128, 38]),
    "SUPER ACTION": bytearray([6, 50, 0, 55]),
    "SUPER JOLLI.": bytearray([6, 50, 52, 57]),
    "SUPER TAIFUN": bytearray([6, 50, 1, 135]),
    "TAIFUN": bytearray([6, 50, 1, 24]),
    "TAIFUN QUICK": bytearray([6, 50, 1, 68]),
    "TEXAS": bytearray([6, 50, 128, 145]),
    "TOOOR": bytearray([6, 50, 128, 151]),
    "TRIPLE POKER": bytearray([6, 50, 129, 6]),
    "TUNING MALLORCA EC1": bytearray([6, 50, 0, 131]),
    "TUNING RIO G": bytearray([6, 50, 0, 37]),
    "TURBO DISC": bytearray([6, 50, 0, 99]),
    "TWIST": bytearray([6, 50, 1, 148]),
    "TAIFUN BISTRO": bytearray([6, 50, 1, 103]),
    "WILD WATER": bytearray([6, 50, 129, 16]),
    "WINNER SQ": bytearray([6, 50, 129, 4]),
    "WORLD CUP 50 SONDERSPIELE": bytearray([6, 50, 1, 25]),
    "WORLD CUP 150 SONDERSPIELE D12 CC1": bytearray([6, 50, 2, 51]),
    "YUPPIE 12 EC1": bytearray([6, 50, 128, 39])
}

# Dictionary for v3Machines
V3_MACHINES = {
    "Ergoline M88": bytearray([6, 50, 18, 50]),
    "Ergoline M90": bytearray([6, 50, 17, 85]),
    "Ergoline M111": bytearray([6, 50, 48, 0]),
    "Ergoline M140": bytearray([6, 50, 19, 105]),
    "Ergoline M202": bytearray([6, 50, 32, 2]),
    "Ergoline M205": bytearray([6, 50, 32, 2]),
    "Casinoline M88": bytearray([6, 50, 17, 84]),
    "Casinoline M90": bytearray([6, 50, 17, 144]),
    "Casinoline M111": bytearray([6, 50, 57, 7]),
    "Casinoline M202": bytearray([6, 50, 32, 18]),
    "Casinoline M205": bytearray([6, 50, 32, 18]),
    "Slimline M88": bytearray([6, 50, 18, 52]),
    "Slimline M90": bytearray([6, 50, 17, 96]),
    "Slimline M111": bytearray([6, 50, 57, 25]),
    "Slimline M202": bytearray([6, 50, 32, 4]),
    "Slimline M205": bytearray([6, 50, 32, 4]),
    "Slantop M88": bytearray([6, 50, 17, 112]),
    "Slantop M90": bytearray([6, 50, 18, 9]),
    "Slantop M111": bytearray([6, 50, 50, 1]),
    "Slantop M140": bytearray([6, 50, 19, 101]),
    "Slantop M202": bytearray([6, 50, 32, 8]),
    "Slantop M205": bytearray([6, 50, 32, 8]),
    "VisionSlantop M88": bytearray([6, 50, 17, 121]),
    "VisionSlantop M111": bytearray([6, 50, 50, 3]),
    "VisionSlantop M202": bytearray([6, 50, 32, 16]),
    "VisionSlantop M205": bytearray([6, 50, 50, 17]),
    "VisionWand M88": bytearray([6, 50, 17, 105]),
    "VisionWand M90": bytearray([6, 50, 18, 7]),
    "VisionWand M111": bytearray([6, 50, 57, 18]),
    "VisionWand M202": bytearray([6, 50, 32, 20]),
    "VisionWand M205": bytearray([6, 50, 32, 20])
}

class AvrDudeRunner:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.avrdude_path = "avrdude"
        self.avrdude_conf = None
        if sys.platform.startswith("win"):
            self.avrdude_path = os.path.join(base_dir, "avrdude.exe")
            self.avrdude_conf = os.path.join(base_dir, "avrdude.conf")

    def build_command(self, processor, programmer, port, eeprom=None, firmware=None, query=False):
        cmd = [self.avrdude_path]
        if self.avrdude_conf:
            cmd += ["-C", self.avrdude_conf]
        cmd += ["-v", "-p", processor, "-c", programmer, "-P", port]
        if query:
            cmd += ["-n"]
        else:
            if eeprom:
                cmd += ["-U", f"eeprom:w:{eeprom}:r"]
            if firmware:
                cmd += ["-U", f"flash:w:{firmware}:r"]
        return cmd

    def run(self, *args, **kwargs):
        command = self.build_command(*args, **kwargs)
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()
            return process.returncode, stdout + stderr
        except Exception as e:
            return 1, str(e)

class EEPROMFlasher:
    def __init__(self):
        self.base_dir = os.getcwd()
        self.avrdude = AvrDudeRunner(self.base_dir)

    def get_serial_ports(self):
        return [(port.device, port.description) for port in serial.tools.list_ports.comports() if port.description != "n/a"]

    def query_cpu_type(self, programmer, port):
        code, output = self.avrdude.run("m328p", programmer, port, query=True)
        if code == 1:
            for line in output.splitlines():
                print(line)
                if "Device signature" in line:
                    sig = line.split("=")[1].split("(")[0].strip().replace(" ", "")
                    return {
                        "1E9205": "m48",
                        "1E920A": "m48p",
                        "1E9001": "1200",
                    }.get(sig)
        return None

    def flash(self, processor, programmer, port, machine_key, machine_serial):
        if not machine_serial.isdigit() or len(machine_serial) != 9:
            return False, "Zulassungsnummer muss genau 9 Ziffern haben."

        if machine_key in V2_MACHINES:
            firmware = os.path.join(self.base_dir, "firmware_v2.bin")
            machine_bytes = V2_MACHINES[machine_key]
        elif machine_key in V3_MACHINES:
            firmware = os.path.join(self.base_dir, "firmware_v3.bin")
            machine_bytes = V3_MACHINES[machine_key]
        else:
            return False, "Ungültiger Automat."

        eeprom_path = os.path.join(self.base_dir, "eeprom.bin")
        if not os.path.exists(firmware) or not os.path.exists(eeprom_path):
            return False, "Firmware oder EEPROM-Datei fehlt."

        # Patch EEPROM
        try:
            with open(eeprom_path, "r+b") as f:
                hex_bytes = bytearray.fromhex("0" + machine_serial)
                f.seek(64)
                f.write(hex_bytes + machine_bytes)
                f.seek(40)
                f.write(bytearray(machine_serial, "ascii"))
        except Exception as e:
            return False, f"EEPROM Fehler: {e}"

        # Run avrdude
        code, output = self.avrdude.run(processor, programmer, port, eeprom=eeprom_path, firmware=firmware)
        return code == 0, output

class EEPROMFlasherGUI:
    def __init__(self, root):
        self.flasher = EEPROMFlasher()
        self.root = root
        self.root.title("EEPROM Flasher")

        # UI elements
        self.serial_var = tk.StringVar()
        self.machine_var = tk.StringVar()
        self.cpu_var = tk.StringVar()
        self.serial_number = tk.StringVar()

        self.build_ui()
        self.update_ports()

    def build_ui(self):
        frame = ttk.Frame(self.root, padding=10)
        frame.grid()

        ttk.Label(frame, text="Serial Port:").grid(row=0, column=0, sticky="w")
        self.port_dropdown = ttk.Combobox(frame, textvariable=self.serial_var, width=30)
        self.port_dropdown.grid(row=0, column=1)
        ttk.Button(frame, text="Erkennen", command=self.update_ports).grid(row=0, column=2)

        ttk.Label(frame, text="Automat:").grid(row=1, column=0, sticky="w")
        machines = list(V2_MACHINES.keys()) + list(V3_MACHINES.keys())
        self.machine_dropdown = ttk.Combobox(frame, values=machines, textvariable=self.machine_var, width=30)
        self.machine_dropdown.grid(row=1, column=1)

        ttk.Label(frame, text="ZlNr:").grid(row=2, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.serial_number, width=30).grid(row=2, column=1)

        ttk.Label(frame, text="Prozessor:").grid(row=3, column=0, sticky="w")
        self.cpu_dropdown = ttk.Combobox(frame, textvariable=self.cpu_var, values=["m48", "m48p", "1200"], width=30)
        self.cpu_dropdown.grid(row=3, column=1)
        ttk.Button(frame, text="CPU erkennen", command=self.detect_cpu).grid(row=3, column=2)

        ttk.Button(frame, text="Flash!", command=self.flash).grid(row=4, column=1, pady=10)

    def update_ports(self):
        ports = self.flasher.get_serial_ports()
        port_list = ["usb"] + [f"{d} ({desc})" for d, desc in ports]
        self.port_map = {"usb": "usb"}
        for d, desc in ports:
            self.port_map[f"{d} ({desc})"] = d
        self.port_dropdown["values"] = port_list
        if ports:
            self.serial_var.set(port_list[0])

    def detect_cpu(self):
        port_label = self.serial_var.get()
        port = self.port_map.get(port_label)
        if not port:
            messagebox.showerror("Fehler", "Kein gültiger Port gewählt.")
            return

        programmer = "usbasp-clone" if port == "usb" else "arduino_as_isp"
        detected = self.flasher.query_cpu_type(programmer, port)
        if detected:
            self.cpu_var.set(detected)
            self.cpu_dropdown.set(detected)
            messagebox.showinfo("Erfolg", f"CPU-Typ erkannt: {detected}")
        else:
            messagebox.showerror("Fehler", "CPU konnte nicht erkannt werden.")


    def flash(self):
        port_label = self.serial_var.get()
        port = self.port_map.get(port_label)
        machine = self.machine_var.get()
        cpu = self.cpu_var.get()
        serial = self.serial_number.get()

        if not all([port, machine, cpu, serial]):
            messagebox.showerror("Fehler", "Bitte alle Felder ausfüllen.")
            return

        programmer = "usbasp-clone" if port == "usb" else "arduino_as_isp"
        success, result = self.flasher.flash(cpu, programmer, port, machine, serial)
        if success:
            messagebox.showinfo("Erfolg", "Flash erfolgreich.")
        else:
            messagebox.showerror("Fehler", result)

if __name__ == "__main__":
    root = tk.Tk()
    app = EEPROMFlasherGUI(root)
    root.mainloop()
