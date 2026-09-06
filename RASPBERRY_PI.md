# CHAOS Arcade — Raspberry Pi 5 installieren und konfigurieren

Diese Anleitung richtet das Messe-Kabinett von null auf ein. Ziel: Raspberry Pi 5 startet, loggt sich automatisch in die grafische Sitzung ein, koppelt den 8BitDo-Arcade-Stick, startet CHAOS Arcade im Vollbild und kommt nach einem Absturz von selbst wieder.

Lies die Schritte der Reihe nach. Befehle, die `sudo` enthalten, brauchen das Administratorpasswort des Pi-Benutzers.

Die Umschaltkombination für das featured Game steht **nicht** auf dem Bildschirm und **nicht** in der `README.md`. Sie steht intern in `MASTER_PROMPT.md` (Abschnitt Operator-Spielwechsel) und unten im Techniker-Kapitel dieser Datei.

---

## 1. Was du brauchst

### Hardware

| Teil | Vorgabe |
|---|---|
| Rechner | Raspberry Pi 5 (4 GB RAM reichen, 8 GB sind bequemer) |
| Speicherkarte | microSD **A2**, mindestens 32 GB, besser 64 GB. Markenware (SanDisk / Samsung). |
| Optional statt SD | NVMe-HAT + SSD — schneller, langlebiger für Dauereinsatz |
| Netzteil | Offizielles **27 W** USB-C-Netzteil (Pi 5). Billige 5-V-Stecker verursachen Throttling und USB-Aussetzer. |
| Display | HDMI-Monitor oder Messe-Panel, nativ 1280×720 oder höher. Das Spiel rendert intern immer 1280×720 und skaliert. |
| HDMI-Kabel | Direkter Anschluss an **HDMI0** (der Port **neben** USB-C). Micro-HDMI → HDMI-Adapter, fest verschrauben. |
| Audio | Über denselben HDMI-Ausgang. Kein extra Lautsprecher nötig, wenn das Panel Ton hat. |
| Stick | **8BitDo DIY Kit** als Arcade-Stick, Bluetooth, Modus **HID / X-input / Android / Windows**. Nicht Switch-Modus. |
| Tastatur | Nur für Installation und Techniker. Nach dem Go-Live abziehen. |
| Gehäuse | Aktiv gekühlt (Lüfter oder Active Cooler). 8–10 Stunden Messe ohne Drosselung. |

### Software vom Arbeitsplatz-PC

- [Raspberry Pi Imager](https://www.raspberrypi.com/software/) (Windows, macOS oder Linux)
- Dieses Git-Repository (`https://github.com/rroollii/CHAOS-PacMan`)
- Optional: USB-Stick, falls der Pi später ohne Netz geklont werden soll

---

## 2. Betriebssystem auf die Karte schreiben

1. microSD in den Arbeitsplatz-PC stecken.
2. Raspberry Pi Imager starten.
3. **Device:** Raspberry Pi 5.
4. **Operating System:**
   - `Raspberry Pi OS (64-bit)` — Variante **with desktop** (nicht Lite).
   - Codename **Bookworm** oder neuer. 64-bit ist Pflicht.
   - Nicht „Lite“, nicht 32-bit, nicht Ubuntu Server. Pygame-Vollbild und Bluetooth-Desktop brauchen die Desktop-Images.
5. **Storage:** die microSD auswählen. Doppelprüfen, nichts anderes überschreiben.
6. Zahnrad **OS customisation** (oder `Ctrl+Shift+X`) öffnen und **genau** das setzen:

   | Feld | Empfehlung |
   |---|---|
   | Hostname | `chaos-arcade` |
   | Username | `chaos` (dieser Name taucht unten in den Pfaden auf) |
   | Password | starkes Passwort, **aufschreiben** |
   | Wireless LAN | nur falls du das Repo über WLAN klonen willst; auf der Messe später aus |
   | Locale | `de_DE.UTF-8`, Tastatur `de`, Zeitzone `Europe/Berlin` |
   | SSH | an, mit Passwort oder besser mit deinem öffentlichen Schlüssel |
   | Telemetrie | aus |

7. **Write** → warten, bis Verify durch ist → Karte sicher auswerfen.

Falls du eine NVMe-SSD nutzt: Imager auf die SSD schreiben (USB-Gehäuse) oder zuerst von SD booten und das Image mit dem Raspberry-Pi-Imager auf die NVMe kopieren (`Copy OS to SSD` in den Pi-Bordmitteln).

---

## 3. Erster Start und Grundkonfiguration

1. Karte in den Pi, HDMI0, Netzteil, Tastatur.
2. Einschalten. Der erste Boot kann 1–2 Minuten dauern (expand filesystem, reboot).
3. Wenn der Desktop-Assistent kommt:
   - Land Deutschland, Sprache Deutsch, Zeitzone Berlin.
   - Passwort nur ändern, wenn Imager es noch nicht gesetzt hat.
   - Updates: **jetzt** ausführen, solange Netz da ist (`sudo apt update && sudo apt full-upgrade -y`).
   - Neustart, wenn der Assistent ihn anbietet.
4. Danach Terminal öffnen und prüfen:

```bash
uname -m          # muss aarch64 sein
cat /etc/os-release
vcgencmd get_throttled   # 0x0 = gut; andere Werte = Netzteil/Temperatur prüfen
```

5. Benutzergruppe für Input/Audio (meist schon gesetzt, schadet nicht):

```bash
sudo usermod -aG video,audio,input,bluetooth,netdev chaos
```

Danach **einmal ab- und anmelden** oder neu starten, sonst greifen die Gruppen nicht.

---

## 4. Grafikstapel: X11 statt Wayland

Raspberry Pi OS Bookworm startet auf dem Pi 5 oft **Wayland** (labwc oder wayfire). Pygame 2 / SDL2 ist im Vollbild unter X11 deutlich zuverlässiger (kein schwarzer Frame, kein Fokusverlust).

1. Terminal:

```bash
sudo raspi-config
```

2. **Advanced Options → Wayland → X11**
3. **System Options → Boot / Auto Login → Desktop Autologin Desktop**
   - Der Benutzer `chaos` muss nach dem Einschalten **ohne Passwort** auf dem Desktop landen. Die systemd-Unit braucht eine lebende grafische Sitzung (`DISPLAY=:0`).
4. Finish → Reboot.

Kontrolle nach dem Reboot:

```bash
echo "$XDG_SESSION_TYPE"    # erwartet: x11
echo "$DISPLAY"             # erwartet: :0
```

Wenn immer noch `wayland` steht: `raspi-config` erneut, X11 wählen, reboot.

### Auflösung

Das Spiel skaliert intern 1280×720 auf die echte Panelgröße. Native Panelauflösung ist besser als erzwungenes 720p (schärferes OSD des Monitors).

Falls das Panel trotzdem die falsche Mode nimmt:

```bash
sudo raspi-config
# Display Options → Resolution → die native Mode des Panels
```

Oder in `/boot/firmware/config.txt` (Bookworm-Pfad, nicht mehr `/boot/config.txt`) **nur wenn nötig**:

```ini
# Nur setzen, wenn der Monitor sonst keine sinnvolle Mode liefert.
hdmi_force_hotplug=1
hdmi_group=1
hdmi_mode=4          # 720p60 — nur Beispiel, an das Panel anpassen
```

Nach jeder Änderung an `config.txt`: Reboot.

Kiosk-Regeln im Spiel selbst (kein Extra-Config nötig):

- Pi: Vollbild `pygame.FULLSCREEN`, Mauszeiger aus.
- Entwicklung: `CHAOS_WINDOWED=1` → Fenster 1280×720.

### Bildschirm darf nicht schlafen

`setup_pi5.sh` schreibt die Autostart-Dateien. Manuell, falls du das Skript noch nicht laufen hattest:

**X11** (nach dem Wechsel oben der Normalfall):

```bash
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/chaos-dpms.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=CHAOS disable blank
Exec=sh -c "xset s off; xset -dpms; xset s noblank; unclutter -idle 0.1 -root"
X-GNOME-Autostart-enabled=true
EOF
```

Sofort testen:

```bash
xset s off
xset -dpms
xset s noblank
xset q | grep -A2 "DPMS"
```

DPMS muss `Disabled` zeigen.

**Falls du auf Wayland bleiben musst:**

- wayfire: in `~/.config/wayfire.ini`

```ini
[idle]
dpms_timeout = -1
```

- labwc: `~/.config/labwc/rc.xml` mit `<offTimeout>0</offTimeout>` im Block `<power>` (legt `setup_pi5.sh` an).

Pixel-Burn-in: die Shell verschiebt HUD und Top-10 nach 180 s Idle alle 30 s um ±2 px. Nicht extra dimmen.

---

## 5. Audio über HDMI

1. `sudo raspi-config` → **System Options → Audio → HDMI**.
2. Desktop: Lautsprecher-Symbol oben rechts → denselben HDMI-Ausgang wählen, Lautstärke ~80 %.
3. Test:

```bash
speaker-test -c 2 -t wav
# oder
aplay /usr/share/sounds/alsa/Front_Left.wav
```

Mixer-Fehler im Spiel werden ignoriert (`audio_enabled = False`). Das Kabinett darf deshalb nicht abstürzen, wenn kein Ton da ist — aber auf der Messe soll HDMI Ton haben.

ALSA-Default (optional, falls Pulse/PipeWire zickt):

```bash
# /etc/asound.conf — nur wenn der HDMI-Gerätname bei `aplay -l` anders heißt
pcm.!default { type hw card 0 device 0 }
ctl.!default { type hw card 0 }
```

Die systemd-Unit setzt `SDL_AUDIODRIVER=alsa`.

---

## 6. Desktop aufräumen (Kiosk-Look)

Nicht zwingend fürs Spiel, aber fürs Kabinett:

1. Taskleiste automatisch ausblenden oder auf dem Messe-User weglassen.
2. Bildschirmschoner in den Desktop-Einstellungen **aus**.
3. Energieoptionen: Display nie ausschalten, Pi nie suspenden.
4. WLAN- und Bluetooth-Popups stummschalten, damit mitten im Attract kein Dialog erscheint.
5. Maus bleibt unsichtbar, sobald das Spiel läuft. `unclutter` versteckt sie auch auf dem Desktop.

Netz auf der Messe:

- Das Spiel hat **keinen** Netzwerkstack.
- WLAN/Ethernet kannst du nach dem Klonen und Update **aus** lassen (`sudo nmcli radio wifi off` oder LAN-Stecker ziehen).
- Nicht nötig, iptables zu verbiegen.

---

## 7. 8BitDo DIY Kit koppeln (genau einmal im OS)

Das Spiel scannt Bluetooth **nicht**. Der Stick muss ein ganz normales HID-Gamepad des Linux-Desktops sein.

### 7.1 Modus am Kit

Am 8BitDo DIY Kit **vor** dem Pairing den richtigen Firmware-Modus wählen (Tastenkombi steht in der Kit-Anleitung, typisch Start + eine Richtungstaste beim Einschalten):

| Modus | LED / Name | Nutzen |
|---|---|---|
| X-input / Windows / Android | oft LED 2 oder „8BitDo …“ ohne „Switch“ | **dieser** |
| macOS | geht meist, aber X-input bevorzugen | Reserve |
| Switch / Nintendo | Gerät heißt oft `Pro Controller` | **verboten** — andere Button-Nummern, Start/Select sitzen falsch |

Nach dem Moduswechsel das Kit **komplett aus- und wieder einschalten**.

Pairing-Modus: Start (oder die kleine Pair-Taste auf der Platine) halten, bis die LED schnell blinkt.

### 7.2 Koppeln per Bluetooth-Applet

1. Desktop oben rechts: Bluetooth → **Turn On**.
2. **Add Device** / **Make Discoverable**.
3. Eintrag des Kits wählen (nicht „Nintendo“, nicht „Switch“).
4. Pair → Trust / „trusted device“.
5. Connect. Der Stick muss als Gamepad erscheinen, nicht als Tastatur.

### 7.3 Koppeln per Terminal (zuverlässiger auf der Messe)

```bash
sudo systemctl enable --now bluetooth
bluetoothctl
```

In der `bluetoothctl`-Shell:

```
power on
agent on
default-agent
scan on
```

Warten, bis die MAC erscheint, z. B. `E4:17:D8:AA:BB:CC  8BitDo Arcade Stick`. Dann (MAC ersetzen):

```
pair E4:17:D8:AA:BB:CC
trust E4:17:D8:AA:BB:CC
connect E4:17:D8:AA:BB:CC
scan off
quit
```

Wenn `pair` nach PIN fragt: `0000` oder einfach Enter. Wenn `Failed to pair: org.bluez.Error.AlreadyExists`:

```
remove E4:17:D8:AA:BB:CC
```

danach erneut pair / trust / connect.

### 7.4 Prüfen, dass Linux ein Gamepad sieht

```bash
ls /dev/input/js0
udevadm info /dev/input/js0 | grep -i name
# optional:
jstest /dev/input/js0
```

In `jstest`:

- D-Pad oder Achse 0/1 muss Werte ändern.
- Action (A) ist typischerweise Button 0, B Button 1.
- Start ist Button 7 oder 9, Select Button 6 oder 8.

`Ctrl+C` beendet `jstest`. Wenn es kein `js0` gibt, ist das Kit nicht als HID verbunden — Modus und Pairing wiederholen, nicht im Spiel weitermachen.

Hot-Plug: Stick aus, wieder an. Pygame erkennt ihn beim nächsten Poll. Trotzdem **vor** dem Messe-Open einmal rebooten, damit BlueZ automatisch reconnectet (`trust` ist dafür die Voraussetzung).

### 7.5 Nach dem Reboot

1. Kit einschalten (nicht extra Pairing-Modus, nur an).
2. LED wird nach ein paar Sekunden dauerhaft.
3. `bluetoothctl info <MAC>` muss `Connected: yes` und `Trusted: yes` zeigen.

Wenn nicht: Kit näher an den Pi, USB-3-Störer weg, einmal `bluetoothctl connect <MAC>`.

---

## 8. Projekt auf den Pi holen

Mit Netz (während der Vorbereitung):

```bash
sudo apt-get install -y git
cd /home/chaos
git clone https://github.com/rroollii/CHAOS-PacMan.git
cd CHAOS-PacMan
```

Ohne Netz: Repo auf einem USB-Stick als Ordner `CHAOS-PacMan` kopieren nach `/home/chaos/CHAOS-PacMan`.

Der Benutzer `chaos` muss Eigentümer sein:

```bash
sudo chown -R chaos:chaos /home/chaos/CHAOS-PacMan
```

Pfade in dieser Anleitung nehmen `/home/chaos/CHAOS-PacMan` an. Wenn dein Username anders ist, überall ersetzen.

---

## 9. `setup_pi5.sh` ausführen

Das Skript installiert Systempakete, legt das Python-venv an, schaltet Screen-Blank aus, schreibt die systemd-Unit und aktiviert sie.

```bash
cd /home/chaos/CHAOS-PacMan
chmod +x setup_pi5.sh
./setup_pi5.sh
```

Dauer: oft 3–8 Minuten (apt + pip). cairosvg braucht Cairo-Dev-Pakete; wenn pip bei cairosvg scheitert, startet das Spiel trotzdem mit Fallback-Geometrie. Die drei Dateien `assets/logo_face.svg`, `assets/logo_mark.svg`, `assets/logo_badge.svg` sollen aber vorhanden sein — dann ist CHAOS der Held.

Was das Skript konkret tut:

1. `apt` für Python 3, pygame (System), Cairo, DejaVu-Font, BlueZ, `xset`, `unclutter`, `joystick`.
2. `python3 -m venv --system-site-packages .venv` im Repo.
3. `pip install -r requirements.txt` in dieses venv.
4. `data/` anlegen (`highscores.json` und `cabinet.json` entstehen beim ersten Schreiben).
5. Autostart gegen Blanking (X11, wayfire, labwc).
6. Unit `/etc/systemd/system/chaos-arcade.service`:
   - `User=chaos`
   - `WorkingDirectory=/home/chaos/CHAOS-PacMan`
   - `ExecStart=/home/chaos/CHAOS-PacMan/.venv/bin/python3 …/main.py`
   - `Restart=always`, `RestartSec=2`
   - `DISPLAY=:0`, `WAYLAND_DISPLAY=wayland-0`, `XDG_RUNTIME_DIR=/run/user/<uid>`
   - Watchdog 15 s; der Prozess sendet alle 10 s `WATCHDOG=1`, wenn systemd `NOTIFY_SOCKET` setzt. Fällt der Prozess um, startet die Unit neu. Ein schwarzes Kabinett nach einem Game-Crash ist damit nicht der Dauerzustand.
7. `systemctl enable chaos-arcade.service`

Manueller Start zum Test **bevor** die Unit läuft:

```bash
cd /home/chaos/CHAOS-PacMan
CHAOS_WINDOWED=1 .venv/bin/python3 main.py
```

Fenster 1280×720, Tastatur reicht: Pfeile oder WASD, Space = Action, Enter = Start. `F11` schaltet Vollbild. Beenden: Linksshift + Q.

Vollbild wie auf der Messe:

```bash
.venv/bin/python3 main.py
```

---

## 10. systemd-Kiosk scharf schalten

Voraussetzung: Desktop-Autologin (Kapitel 4) ist aktiv. Sonst findet der Dienst kein `:0`.

```bash
sudo systemctl daemon-reload
sudo systemctl enable chaos-arcade.service
sudo systemctl start chaos-arcade.service
sudo systemctl status chaos-arcade.service
```

`active (running)` und im Journal keine Python-Tracebacks:

```bash
journalctl -u chaos-arcade.service -e
```

Nach einem Reboot muss das Spiel **ohne Tastendruck** im Vollbild stehen. Wenn die Unit zu früh startet (noch kein `:0`):

```bash
sudo systemctl restart chaos-arcade.service
```

und optional in der Unit (nur falls nötig) eine Verzögerung:

```ini
[Service]
ExecStartPre=/bin/sleep 5
```

Danach `sudo systemctl daemon-reload && sudo systemctl restart chaos-arcade.service`.

Unit anhalten (Techniker, Desktop zurück):

```bash
sudo systemctl stop chaos-arcade.service
```

---

## 11. Was nach dem Start passieren muss

1. Schwarzer Arcade-Hintergrund, Logo, Titel **PAC-MAN**, Zeile `ISS DAS SHELFWARE`.
2. Rechts die Top-10 dieses Titels, auch leer (`---` / `000000`).
3. Unten blinkt `START SPIELEN`. Keine Pfeile, kein Carousel, keine Nachbartitel.
4. 12 s ohne Input: Attract **nur** von Pac-Man, HUD zeigt `DEMO`, Top-10 bleibt lesbar.
5. Jeder Stick- oder Tastatur-Input: zurück zum Idle desselben Titels.
6. Start oder Action: Spiel startet. Top-10 verschwindet, HUD zeigt Score / Leben / Level.
7. Game Over: Overlay + Tafel. Qualifizierter Score (> 0 und Top-10) → nach 1,2 s Namenseingabe. Sonst zurück zum Idle.
8. Name: 3–8 Zeichen `A–Z 0–9 -`. Unter 3 Zeichen kein Absenden. Timeout 20 s **verwirft** den Score (kein `AAA`, kein anonymer Eintrag).
9. 30 s Inaktivität im Spiel oder auf Game Over: Idle, **kein** Highscore aus einer abgebrochenen Runde.

Highscores liegen in `data/highscores.json`, das featured Game in `data/cabinet.json`. Beide Dateien sind gitignored und überleben Reboots.

---

## 12. Techniker-Bedienung (nicht auf das Gehäuse kleben)

Kein HUD-Text erklärt diese Tasten.

| Aktion | Tastatur | 8BitDo |
|---|---|---|
| Featured Game weiter / zurück | **Left-Shift gehalten** + Links / Rechts | **Select oder Start gehalten** + Links / Rechts |
| Direktwahl Katalog 1…7 | Tasten `1` … `7` | — |
| Highscores aller Titel löschen | Left-Shift + `R` | — |
| Vollbild umschalten | `F11` | — |
| Prozess beenden | Left-Shift + `Q` | — |

Katalogreihenfolge: Pac-Man → Donkey Kong → Snake → Bubble Shot → Frogger → Invaders → Breakout → Pac-Man.

Der Wechsel wirkt im Idle, im Attract und auf Game Over **ohne** anstehende Namenseingabe. Mitten im Spiel und in der Namenseingabe ist er gesperrt. Nach dem Wechsel erscheint ein kurzer Cyan-Rahmen, auf stdout steht `[operator] featured=SNAKE`. `data/cabinet.json` wird sofort geschrieben — nach Stromausfall kommt dasselbe Spiel wieder.

Besucher-Links/Rechts darf das Spiel **nicht** wechseln. Deshalb Shift bzw. gehaltenes Start/Select.

---

## 13. Messe-Checkliste (30 Minuten vor Open)

1. Offizielles 27-W-Netzteil, HDMI0, Kühlung dreht.
2. `vcgencmd measure_temp` unter 75 °C im Idle.
3. `systemctl is-active chaos-arcade.service` → `active`.
4. Bildschirm blankt in 3 Minuten **nicht**.
5. HDMI-Ton hörbar.
6. Stick einschalten, 5 s warten, D-Pad bewegt Pac-Man bzw. startet das Spiel.
7. Eine Runde spielen, Namen eintragen, Pi neu starten, Name ist noch da.
8. Featured Game auf den Messe-Titel stellen (Techniker-Kombo), reboot, derselbe Titel kommt wieder.
9. Tastatur aus dem Kabinett nehmen.
10. WLAN aus, wenn nicht gebraucht.

---

## 14. Wartung und Update

Neues Release (mit Netz):

```bash
sudo systemctl stop chaos-arcade.service
cd /home/chaos/CHAOS-PacMan
git pull --ff-only
./setup_pi5.sh          # nur nötig bei neuen Systempaketen / requirements
sudo systemctl start chaos-arcade.service
```

Highscores und `cabinet.json` nicht committen und nicht löschen, wenn du nur Code aktualisierst.

Highscores mutwillig leeren: Techniker-Kombo Shift+R **oder** Datei löschen:

```bash
rm -f /home/chaos/CHAOS-PacMan/data/highscores.json
```

Das featured Game bleibt in `cabinet.json`.

SD-Karte klonen (zweiter Kiosk): Pi aus, Karte im Arbeitsplatz mit Imager oder `dd` duplizieren, auf dem Klon Hostname ändern (`sudo raspi-config`), 8BitDo **neu** pairen (andere Bluetooth-MAC-Bindung).

---

## 15. Fehlerbehebung

### Schwarzer Bildschirm nach Boot, kein Spiel

```bash
echo "$DISPLAY"
sudo systemctl status chaos-arcade.service
journalctl -u chaos-arcade.service -b --no-pager
```

Häufig: kein Autologin → kein `:0`. Kapitel 4. Oder Unit zu früh: `ExecStartPre=/bin/sleep 5`.

### Spiel startet, Stick tot

- `ls /dev/input/js0` — fehlt das Gerät, ist BlueZ das Problem, nicht Pygame.
- Kit im Switch-Modus? Neu in X-input pairen.
- `bluetoothctl info` → Connected/Trusted.
- Tastatur als Kontrolle: Pfeile müssen immer gehen. Wenn Tastatur wirkt und Stick nicht, Mapping/Pairing.

### Stick driftet oder Attract startet nicht

Analog unter der Deadzone 0,45 zählt nicht als Input. Defektes DIY-Poti dauerhaft über der Deadzone hält den Idle-Timer fest. Dann Digital-HAT nutzen oder Stick tauschen.

### cairosvg / Logo fehlt

Logzeilen beim Start:

```
[assets] FACE loaded via cairosvg: …
```

oder `using fallback geometry`. Fallback ist erlaubt. Fehlende Systempakete: `sudo apt install libcairo2-dev` und `./setup_pi5.sh` nochmal.

### Unit restartet in einer Schleife

Journal lesen. Typisch: pygame kann kein Display öffnen (Wayland/X11). Auf X11 wechseln, als User `chaos` einmal `echo $DISPLAY` im Desktop-Terminal prüfen, Unit-Environment anpassen.

### Bild schläft nach 10 Minuten

`xset q` — DPMS noch an? Autostart-Desktop-Datei vorhanden? Unter Wayland die idle-Files aus Kapitel 4. Pi-OS „Screen blanking“ in raspi-config / Desktop-Settings zusätzlich aus.

### Ton weg

raspi-config Audio = HDMI, Panel-Stummschaltung, `pactl get-default-sink`. Spiel läuft ohne Mixer weiter.

### Highscore weg nach Stromzug

`data/` muss auf der SD beschreibbar sein (`df -h .`, nicht read-only). Atomare Writes nutzen `highscores.json.tmp` + `os.replace`. Bei voller SD schlägt der Write fehl — Platz schaffen.

### Performance unter 50 FPS

- Nur den Desktop-Compositor, kein Chromium im Hintergrund.
- `vcgencmd get_throttled` und Temperatur.
- Kein 4K-Panel erzwingen, wenn das Panel 1080p kann.
- Interne Surface bleibt 1280×720; riesige 4K-Skalierung kostet etwas, bleibt auf Pi 5 üblicherweise über Budget.

### Notaus / Prozess hängt

Tastatur: Shift+Q. Sonst SSH:

```bash
sudo systemctl restart chaos-arcade.service
```

Hart: Strom nur als letzte Option (SD-Wear, Journal).

---

## 16. Kurzreferenz der Dateien auf dem Pi

```
/home/chaos/CHAOS-PacMan/
  main.py                 Einstieg
  setup_pi5.sh            dieser Installer
  RASPBERRY_PI.md         diese Anleitung
  requirements.txt
  .venv/                  Python-Umgebung
  assets/logo_*.svg       CHAOS-Logos
  data/highscores.json    Top-10 pro Spiel (Laufzeit)
  data/cabinet.json       featured GameId (Laufzeit)

/etc/systemd/system/chaos-arcade.service
~/.config/autostart/chaos-dpms.desktop
```

Entwicklung auf einem normalen PC (nicht Pi):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
CHAOS_WINDOWED=1 python3 main.py
```

Python 3.11 oder neuer, Pygame 2. Tastatur allein reicht für alle sieben Titel.
