# CHAOS Arcade

Messe-Kiosk mit sieben Kurzspielen: Pac-Man, Donkey Kong, Snake, Bubble Shot, Frogger, Invaders und Breakout.

Der Held ist überall das CHAOS-Logo. Wo Beine nötig sind, sind das Strichmännchen-Linien. Gegner gehören zum Lizenzchaos; jedes Spiel trägt die Microsoft-Vier-Quadrate als Primitive.

Ein Titel ist jeweils freigeschaltet. Besucher starten, spielen und hinterlegen bei einem Top-10-Score ihren Namen. Die Bestenliste des aktuellen Spiels bleibt sichtbar, solange nicht gespielt wird.

Das verbindliche Pflichtenheft steht in [`MASTER_PROMPT.md`](MASTER_PROMPT.md).  
Die komplette Raspberry-Pi-5-Installation (OS flashen, Display, Bluetooth, systemd) steht in [`RASPBERRY_PI.md`](RASPBERRY_PI.md).

## Lokal starten

Python 3.11+ und eine grafische Sitzung:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
CHAOS_WINDOWED=1 python3 main.py
```

Ohne Fenster-Variable startet das Spiel im Vollbild. Der Mauszeiger bleibt aus.

| Taste | Funktion |
|---|---|
| Pfeile oder WASD | Richtung |
| Space oder Ctrl | Action (Sprung, Schuss, Bestätigen) |
| Enter | Start |
| F11 | Vollbild umschalten |

Die drei Dateien unter `assets/` sind optional. Fehlen sie, zeichnet die Engine Fallback-Geometrie.

## Raspberry Pi 5

```bash
chmod +x setup_pi5.sh
./setup_pi5.sh
```

Danach entweder `python3 main.py` bzw. das venv-Python, oder den von `setup_pi5.sh` angelegten Dienst `chaos-arcade.service`. Alle Schritte von Image bis 8BitDo-Pairing: [`RASPBERRY_PI.md`](RASPBERRY_PI.md).

## Spiele

| Titel | Ziel |
|---|---|
| PAC-MAN | Shelfware fressen, Auditoren ausweichen |
| DONKEY KONG | Zum Vertrag klettern, Rollen überspringen |
| SNAKE | Ungenutzte Seats fressen, nicht in sich selbst |
| BUBBLE SHOT | SKUs zu dreier Gruppen sortieren |
| FROGGER | Quer durchs Renewal in fünf Nester |
| INVADERS | Die Audit-Welle abschießen |
| BREAKOUT | Den Lock-in durchbrechen |

Highscores liegen in `data/highscores.json`, getrennt pro Titel, nur mit Namen (3–8 Zeichen).
