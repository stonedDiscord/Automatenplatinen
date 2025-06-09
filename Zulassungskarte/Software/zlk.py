import serial
# pip install pyserial
import serial.tools.list_ports
import subprocess
import os
import sys

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

class EEPROMFlasher:
    def __init__(self):
        self.base_dir = os.getcwd()

    def get_available_serial_ports(self):
        if sys.platform.startswith("win") or sys.platform.startswith("linux") or sys.platform.startswith("darwin"):
            return [(port.device, port.description) for port in serial.tools.list_ports.comports() if port.description != "n/a"]
        else:
            raise EnvironmentError("Das Betriebssystem kenne ich nicht.")

    def is_serial_port_available(self, serial_port):
        try:
            with serial.Serial(serial_port) as ser:
                ser.close()
            return True
        except (serial.SerialException, OSError):
            print(f"{RED_TEXT}Fehler: Serial Port {serial_port} nicht verfügbar.{RESET}")
            return False

    def change_eeprom_characters(self, file_path, start, new_chars):
        try:
            with open(file_path, "r+b") as file:
                file.seek(start)
                file.write(new_chars)
        except IOError as e:
            print(f"{RED_TEXT}Fehler beim Öffnen des EEPROMs: {e}{RESET}")

    def flash_eeprom(self, serial_port, machine_key, processor=None, machine_serial=None):
        if len(machine_serial) != 9 or not machine_serial.isdigit():
            print(f"{RED_TEXT}Fehler: Bitte genau 9 Ziffern eingeben.{RESET}")
            return False

        if not machine_key:
            print(f"{RED_TEXT}Fehler: Ungültiger Automat.{RESET}")
            return False

        if serial_port != "usb" and not self.is_serial_port_available(serial_port):
            print(f"{RED_TEXT}Fehler: Irgendwas stimmt mit dem Serial Port nicht.{RESET}")
            return False

        firmware_file_path = os.path.join(self.base_dir, "firmware_v2.bin" if machine_key in V2_MACHINES else "firmware_v3.bin")
        eeprom_file_path = os.path.join(self.base_dir, "eeprom.bin")

        if not os.path.exists(firmware_file_path):
            print(f"{RED_TEXT}Fehler: Datei {os.path.basename(firmware_file_path)} fehlt.{RESET}")
            return False

        if not os.path.exists(eeprom_file_path):
            print(f"{RED_TEXT}Fehler: Datei {os.path.basename(eeprom_file_path)} fehlt.{RESET}")
            return False

        hex_string = "0" + machine_serial
        hex_bytes = bytearray.fromhex(hex_string)
        machine_bytes = V2_MACHINES[machine_key] if machine_key in V2_MACHINES else V3_MACHINES[machine_key]
        new_chars = hex_bytes + machine_bytes

        self.change_eeprom_characters(eeprom_file_path, 64, new_chars)
        self.change_eeprom_characters(eeprom_file_path, 40, bytearray(machine_serial, "ascii"))

        print("Lege los...")

        avrdude_path = "avrdude"
        if sys.platform.startswith("win"):
            avrdude_path = os.path.join(self.base_dir, "avrdude.exe")
        avrdude_conf_path = os.path.join(self.base_dir, "avrdude.conf")

        programmer_argument = "usbasp-clone" if serial_port == "usb" else "arduino_as_isp"

        return self.run_avrdude(avrdude_path, avrdude_conf_path, processor, programmer_argument, serial_port, eeprom_file_path, 
firmware_file_path)

    def run_avrdude(self, avrdude_path, avrdude_conf_path, processor, programmer_argument, serial_port, eeprom_file_path=None, 
firmware_file_path=None):
        avrdude_command = [
            avrdude_path,
            "-C", avrdude_conf_path,
            "-v",
            "-p", processor,
            "-c", programmer_argument,
            "-P", serial_port
        ]

        if eeprom_file_path:
            avrdude_command.extend(["-U", f"eeprom:w:{eeprom_file_path}:r"])
        
        if firmware_file_path:
            avrdude_command.extend(["-U", f"flash:w:{firmware_file_path}:r"])

        try:
            process = subprocess.Popen(avrdude_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            for line in process.stdout:
                print(line, end="")
            for line in process.stderr:
                print(line, end="")

            process.wait()
            if process.returncode == 0:
                print(f"{GREEN_TEXT}Erfolgreich.{RESET}")
                return True
            else:
                print(f"{RED_TEXT}Fehler.{RESET}")
                return False
        except Exception as e:
            print(f"{RED_TEXT}Fehler: {e}{RESET}")
            return False

    def query_cpu_type(self, avrdude_path, avrdude_conf_path, programmer_argument, serial_port):
        avrdude_command = [
            avrdude_path,
            "-C", avrdude_conf_path,
            "-v",
            "-c", programmer_argument,
            "-P", serial_port,
            "-n",  # No operation
            "-p", "m328p"  # Query the device signature
        ]

        try:
            process = subprocess.Popen(avrdude_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            output = process.communicate()[1]
            
            if process.returncode == 1:
                lines = output.splitlines()
                for line in lines:
                    if "Device signature" in line:
                        signature = line.split("=")[1].split("(")[0]
                        signature = signature.strip().split(" ")
                        if len(signature) == 3:
                            processor_signature = "".join(signature)
                            # Map the device signature to a known processor type
                            signature_map = {
                                "1E9205": "m48",
                                "1E920A": "m48p",
                                "1E9001": "1200",
                            }
                            return signature_map.get(processor_signature)
            else:
                print(f"{RED_TEXT}Fehler beim Abfragen der CPU-Signatur.{RESET}")
        
        except Exception as e:
            print(f"{RED_TEXT}Fehler: {e}{RESET}")

        return None

def get_serial_port_input(available_ports):
    while True:
        try:
            serial_port_number = int(input("Bitte einen Anschluss auswählen: "))
            if 1 <= serial_port_number <= len(available_ports):
                return available_ports[serial_port_number - 1][0]
            elif serial_port_number == 0:
                return "usb"
            else:
                print(f"{YELLOW_TEXT}Den gibt es nicht.{RESET}")
        except ValueError:
            print(f"{YELLOW_TEXT}Bitte eine Zahl eingeben.{RESET}")

def get_machine_input(all_machines):
    while True:
        try:
            machine_key_number = int(input("Nummer des Automaten: "))
            if 1 <= machine_key_number <= len(all_machines):
                return all_machines[machine_key_number - 1]
            else:
                print(f"{YELLOW_TEXT}Ungültige Nummer.{RESET}")
        except ValueError:
            print(f"{YELLOW_TEXT}Bitte eine Zahl eingeben.{RESET}")

def get_machine_serial_input():
    while True:
        machine_serial = input("Zulassungsnummer (9 Ziffern): ")
        if len(machine_serial) == 9 and machine_serial.isdigit():
            return machine_serial
        else:
            print(f"{YELLOW_TEXT}Ungültig. Bitte GENAU 9 Ziffern.{RESET}")

def main():
    flasher = EEPROMFlasher()

    available_ports = flasher.get_available_serial_ports()
    print("Verfügbare Anschlüsse:")
    print(" 0. USBASP")
    for index, port in enumerate(available_ports, start=1):
        if isinstance(port, tuple):
            device, description = port
            print(f" {index}. {device} ({description})")
        else:
            print(f" {index}. {port}")

    serial_port_number = get_serial_port_input(available_ports)
    print(serial_port_number)
    if not serial_port_number:
        return

    all_machines = list(V2_MACHINES.keys()) + list(V3_MACHINES.keys())
    print("Automaten:")
    for index, key in enumerate(all_machines, start=1):
        print(f" {index}. {key}")

    machine_key = get_machine_input(all_machines)
    if not machine_key:
        return

    avrdude_path = "avrdude"
    if sys.platform.startswith("win"):
        avrdude_path = os.path.join(flasher.base_dir, "avrdude.exe")
    avrdude_conf_path = os.path.join(flasher.base_dir, "avrdude.conf")

    programmer_argument = "usbasp-clone" if serial_port_number == "usb" else "arduino_as_isp"

    # Query the CPU type
    processor_type = flasher.query_cpu_type(avrdude_path, avrdude_conf_path, programmer_argument, serial_port_number)
    
    if not processor_type:
        print(f"{RED_TEXT}Fehler: Prozessor-Typ konnte nicht ermittelt werden.{RESET}")
        return

    print(f"Ermittelter Prozessor-Typ: {processor_type}")

    machine_serial = get_machine_serial_input()

    while not flasher.flash_eeprom(serial_port_number, machine_key, processor=processor_type, machine_serial=machine_serial):
        retry = input("Fehlgeschlagen. Nochmal versuchen? (y/n): ").strip().lower()
        if not (retry == "y" or retry == "z" or retry == "j"):
            break

if __name__ == "__main__":
    main()
