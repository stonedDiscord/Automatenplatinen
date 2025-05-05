# Programmierstation


## Aufbau
Anfangen würde ich immer mit den flachsten Bauteilen, in diesem Fall also Widerstände, Kondensatoren und die Diode.
Es sind für fast jedes Bauteil je eine THT und eine SMD Position vorhande, davon muss natürlich nur je eine bestückt werden.

Die Werte der 3x 330 Ohm Widerständen und der Kondensatoren müssen nicht so genau stimmen, da kann man auch nehmen was grad da ist.
Die 3 Widerstände sind die Vorwiderstände der LEDs, diese sollten mindestens 270 Ohm und nicht mehr als 1 kOhm betragen, bei zu viel werden die LED zu dunkel.
Die Kondensatoren sind zur Pufferung, diese sollten mindestens 47uF und 10V haben, beide Werte dürfen höher (aber nicht kleiner) sein.
Die Diode sollte eine Spannung unter 1V im Datenblatt haben und mindestens 0.3A aushalten können.
Die 1 Ohm Widerstände müssen wirklich 1 Ohm haben, die zu brücken wird nicht funktionieren.

Als nächstes kommt der 74HC14. Dieser wird nur für die Soundkarten Funktionen gebraucht und kann entfallen falls man die nicht braucht.

Als nächstes das INA226-Modul.
Achtet bitte darauf das die Belegung der Pins mit denen auf der Platine übereinstimmt, es gibt hier mehrere Verianten von dem Modul.
Konkret geht es da um die SDA und SCL Pins.
Für eine Spannungsüberwachung/Kalibrierhilfe in einer zukünftigen Software-Version sollte man ein Kabel zwischen den Pins VBS und IN- anlöten.

Nun kommt das Step-Up Modul mit den 4 Pins.
Dieser ist etwas tricky zu montieren,
ich habe die Pins abgeknipst, in die Löcher gesteckt, das Modul oben drauf und dann von oben fest gelötet.
Dann festhalten und von der Unterseite festlöten.

Als nächstes der Arduino. Diesen am besten vorher schon programmieren, das kann man online unter https://automatenunsinn.github.io/isp.html oder
man lädt sich die Hex-Datei aus dem Ordner https://github.com/Automatenunsinn/automatenunsinn.github.io/tree/master/public/hex runter.
Einer der 2 rechten Dateien, bei den Arduino-Klonen den Knopf mit Alt drauf.
Festlöten hier ähnlich wie beim Step-Up, die ganze Pin Reihe in die Löcher stecken, den Arduino drauf und anlöten.
Hier müssen theoretisch nicht alle Pins gelötet werden, ich kann auch noch mal ein Bild machen wo man sieht welche das sind.

Nun noch das TTL Serial USB Modul neben dem Arduino. Hier bitte auch auf die Beschriftung achten.
Bei den Modulen die Ich eingekauft habe sind 5V und GND vertauscht,
also die beiden Pins einfach frei lassen und mit den beigefügten Drähten in die Löcher für 5V und Minus von Kondensator C2.

Dann noch die 3 LED einlöten und wir können testen und kalibrieren.
Einfach ein USB-Kabel in den Arduino stecken und die 3 LED sollten nacheinander aufblitzen.
Die grüne LED sollte dann anfangen zu "atmen".
Falls die rote LED aufleuchtet konnte der Arduino das INA-Modul nicht finden, in dem Fall die INA 0x44 Variante der Software (oder umgekehrt) probieren.
Falls dann alles passt, die Station an lassen und mit einem Multimeter an die beiden Ausgangspins des Step-Ups.
Hier muss der Poti mit einem kleinen Schlitz-Schraubenzieher nach links gedreht werden, evtl so 20 mal bis sich am Multimeter etwas tut.
Die Spannung muss auf 12.3V eingestellt werden.
Eventuell gibt es bald auch noch ein Softwareprogramm, welches das automatisch messen kann ohne Multimeter.
Damit ist die Kalibrierung fertig.

Nun kann noch der Schalter reingelötet werden falls man den für die Soundkarten braucht.
Danach die Stecker für Atmel, ZLK und Soundkarte.
Zu allerletzt die Stecker für die Datenbank.

Fertig :)
