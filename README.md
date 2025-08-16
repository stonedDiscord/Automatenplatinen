# Automatenplatinen
Alle möglichen Sachen die ich als Teil des Spielautomaten Hobby so nachgebaut habe.

Diskussionen rund um die Entwicklung führe ich generell auf dem Automatentreff Discord:
https://discord.gg/CEFa4MkQmW

Fertig sind:
- Initialisierer: ein Init-Stecker für weiße CPUs. Hat 2 Taster.
- ServiceTastaturWeissFake - das ist ein simpler Nachbau einer Servicetastatur für die weiße CPU. Dadurch das sie simpler ist, sind überall die Zahl 0 auf halber Helligkeit zu sehen. Verwenden lässt sie sich trotzdem.
- ZLKhalter: Anscheinend beraubt jeder, der Zulassungskarten beschreibt, einen Automaten um diesen Halter. Katastrophe.
- Zulassungskarte: Neuere mit Atmega48.

Die Gerber werde ich bei den Releases hochladen.

Ungetestet:
- FlashUniversal: Eine Pogo-Pin Platine für Datenbanken.
- LEDLamp: Das sind LEDs die in die Sockel dieser 6V 2W Glühbirnchen passen und einen Kondensator mit dabei haben damit sie langsam ausgehen wie die alten Birnen.
- LPTastatur: das ist die Tastatur für einen NSM Drucker.
- NSMAdapter: Ein Adapter der die Pins vom Timekeeper auf NSM Spielmodulen so nach außen führt das man sie mit einem EEPROM Brenner beschreiben kann.
- PCauslese: Ein Auslese-Adapter mit einem ESP-01. Soll kompatibel mit den ganz alten Geräten werden und die Uhrzeit automatisch setzen und die ausgelesenen Daten zwischenspeichern.
- ProgrammierStation: Arduino ISP Programmer und Seriell auf einem Board mit Stromversorgung.
- ST25: Tastatur für NSM Geräte
- SoundkartenProg: Ein Inverter für den seriellen Anschluss von kleinen Soundkarten.
- Tasterplatine: Fast das gleiche wie die LEDLamp aber mit einem Taster dabei. Für alte Geräte mit weißer CPU.

Schrott:
- DB1MBRedesign: Forschung wo die Pins der Datenbank hingehen.
- DBV: Das ist ein Stecker der in den CPU-Sockel von Bally Wulff Spielmodulen kommt und dann die RTC und den SRAM beschreiben kann, ähnlich dem Datenbankverwalter
- E60: Hier wollt ich mal schauen wie die Konvertierung der Logik-Level umgesetzt wurde. Das Ergebnis: Ein Transistor halt. Naja.
- Programmierboard: Ein User hat das Ding auf eBay geschossen und wollte wissen was es kann.
- Serial: die ProgrammierStation aber mit WLAN, liegt auf Eis bis die normale ProgrammierStation fertig ist.
- Soundkarte: Irgendeine Adapter, nicht so wichtig.
- Spielmodul: Forschung für den DBV wo die ganzen Leiterbahnen eigentlich hingehen und wie man den RTC anspricht.
- ZLKalt: Zulassungskarte mit AT90
