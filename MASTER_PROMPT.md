# CHAOS PacMan — Master-Prompt / System-Instruction Set

**Dokumenttyp:** Pflichtenheft + Self-Instruction Set für Code-Generierung  
**Zielplattform:** Raspberry Pi 5 (64-bit Raspberry Pi OS)  
**Stack:** Python 3.11+ / Pygame 2  
**Eingabe:** 8BitDo DIY Kit (Bluetooth Arcade-Stick) + Tastatur-Pfeiltasten  
**Spieler-Asset:** `assets/logo.svg` (Firmenlogo, Vektor)  
**Betriebsart:** Unbeaufsichtigtes Messe-Kiosk am digitalen Pult  

Dieses Dokument ist verbindlich. Jede nachfolgende Implementierung (`main.py` und Hilfsmodule) muss sich **wortgetreu** an diese Vorgaben halten. Abweichungen sind nur zulässig, wenn sie einen Laufzeitfehler auf dem Raspberry Pi 5 verhindern — und müssen dann im Code kommentiert werden.

---

## 0. Nicht verhandelbare Leitplanken

### 0.1 Betriebsziel

CHAOS PacMan ist ein **30–90-Sekunden-Mitmach-Spiel** im Pac-Man-Stil. Ein Messebesucher greift zum Arcade-Stick, spielt eine Runde, sieht den Score, und das Gerät kehrt selbstständig in den Lockbildschirm zurück. Es gibt **kein** Menü mit Dateipfaden, **kein** Beenden über UI, **kein** Vollbild-Verlassen außer über ein verstecktes Operator-Hotkey (siehe 2.5).

### 0.2 Hardware-Annahmen

| Komponente | Vorgabe |
|---|---|
| Rechner | Raspberry Pi 5, 4 GB oder 8 GB RAM |
| OS | Raspberry Pi OS Bookworm (64-bit), Desktop oder Lite + X11/Wayland |
| Display | Landschaft, Zielauflösung **1280×720** intern; skaliert auf das angeschlossene Pult-Display |
| Audio | Optional; Sound darf fehlen ohne Crash |
| Controller | 8BitDo DIY Kit als Standard-HID-Gamepad über Bluetooth |
| Fallback-Eingabe | Tastatur: Pfeiltasten + Enter/Space + Esc |

### 0.3 Performance-Budget (Pi 5)

- Feste Logik-Tickrate: **60 Hz** (`CLOCK.tick(60)`).
- Kein per-frame SVG-Re-Rendering. Vektoren werden **einmal** beim Start (und bei Fenster-Resize) in Surfaces gerastert.
- Maximal **eine** vollständige Maze-Redraw-Komposition pro Frame; Dots/Pellets als Dirty-Rects oder Layer-Cache.
- Keine Blocking-I/O im Game-Loop. Highscore-Schreiben erfolgt atomar und kurz.
- Ziel: stabil ≥ 50 FPS auf Pi 5 bei 1280×720.

### 0.4 Code-Qualität

- Eine klare Modulstruktur (siehe 0.5). `main.py` ist der Einstieg, nicht der gesamte Monolith, **außer** die erste lauffähige Version darf bewusst in `main.py` gebündelt sein, solange die Sektionen durch Kommentarbanner getrennt und die Klassen identisch benannt sind.
- Typ-Hints an allen öffentlichen Funktionen und Klassenmethoden.
- Keine Magic Numbers ohne benannte Konstanten im Block `CONFIG`.
- Keine Netzwerkzugriffe.
- Keine Telemetrie.
- UTF-8, Linux-Zeilenenden.
- Lauffähig **ohne** `logo.svg` (Fallback-Renderer ist Pflicht).

### 0.5 Verbindliche Dateistruktur

```
CHAOS_PacMan/
├── main.py                 # Einstieg + Game-Loop
├── config.py               # Alle Konstanten, Farben, Timing, Grid
├── input_map.py            # Keyboard + Gamepad-Mapping
├── assets_loader.py        # SVG-Pipeline + Fallback-Logo
├── maze.py                 # Grid, Kollision, Dots, Tunnel
├── player.py               # Spieler-Entität
├── ghosts.py               # Geister + KI
├── states.py               # State-Machine
├── highscore.py            # JSON Persistenz
├── attract.py              # Attract-Mode Demo
├── assets/
│   └── logo.svg            # Firmenlogo (kann fehlen)
├── data/
│   └── highscores.json     # wird zur Laufzeit erzeugt
├── requirements.txt
├── setup_pi5.sh            # Installationsskript für Raspberry Pi 5
├── MASTER_PROMPT.md        # dieses Dokument
└── README.md
```

Die **erste vollständige Auslieferung** darf alle Module in `main.py` vereinen, **muss** aber dieselben Klassen-/Funktionsnamen verwenden, damit ein späterer Split ohne API-Bruch möglich ist.

### 0.6 Visuelle Identität (Arcade / CHAOS)

- Hintergrund: tiefes Anthrazit `#0B0D10`.
- Wände: neon-cyan `#2DE2E6` mit dunklem Innenfill `#12161C`.
- Dots: warmes Weiß `#F4F1EA`.
- Power-Pellets: pulsierendes Bernstein `#FFB703`.
- HUD: monospace, hoher Kontrast, große Zahlen (Messe-Lesbarkeit ab 1,5 m).
- Geisterfarben (fest): Blinky `#FF3B3B`, Pinky `#FF7AD9`, Inky `#3BD1FF`, Clyde `#FF9F1C`.
- Kein Comic-Pac-Man-Sprite. Der Spieler **ist** das Firmenlogo.

---

## 1. Asset-Pipeline & SVG-Rendering

### 1.1 Quelle und Verträge

- Primärpfad: `assets/logo.svg`.
- Das SVG gilt als **quadratisch normiert**. Liegt ein nicht-quadratisches ViewBox vor, wird der Inhalt **proportional** in ein Quadrat gefittet und zentriert (Letterbox transparent, niemals gestreckt).
- Zielgröße der Spieler-Surface: `PLAYER_SIZE = TILE_SIZE - 4` Pixel (2 px Luft pro Seite im Tile).
- `TILE_SIZE = 32` bei internem Raster. Maze-Zellen sind 32×32 CSS-Pixel der internen Oberfläche.

### 1.2 Ladestrategie (verbindliche Reihenfolge)

Die Loader-Klasse heißt `LogoAsset`. Methode: `LogoAsset.load(path: Path, size: int) -> pygame.Surface`.

**Stufe A — cairosvg (bevorzugt auf Pi 5):**

```
SVG-Bytes → cairosvg.svg2png(bytestring=..., output_width=size*2, output_height=size*2)
         → PNG-Bytes → pygame.image.load(BytesIO(...)).convert_alpha()
         → smoothscale auf (size, size)
```

Begründung: 2×-Supersampling reduziert Treppeneffekte an Logo-Kanten. `output_width/height` erzwingt quadratisches Rastern unabhängig von ViewBox-Seitenverhältnis; cairosvg letterboxt intern, sofern `svg2png` mit identischen Maßen aufgerufen wird. Zusätzlich wird das PNG nach dem Load auf ein echtes Quadrat zentriert, falls cairosvg das Seitenverhältnis erhält:

1. Lade Surface.
2. Berechne `scale = size / max(w, h)`.
3. Skaliere proportional.
4. Blitte auf eine transparente `size×size`-Surface, zentriert.

**Stufe B — pygame / SDL_image (Fallback, wenn cairosvg fehlt oder scheitert):**

- `pygame.image.load(path)` nur wenn die lokale Pygame-Build SVG kann (unsicher auf Pi).
- Bei Exception: weiter zu Stufe C.

**Stufe C — geometrischer Fallback (immer verfügbar):**

Wenn `assets/logo.svg` fehlt **oder** Stufe A und B scheitern, zeichnet `render_fallback_logo(size: int) -> pygame.Surface` ein stilisierter CHAOS-Marken-Avatar rein mit Pygame:

- Kreis-Körper, Radius `size * 0.46`, Fill `#F4F1EA`, 2 px Outline `#2DE2E6`.
- Pac-Man-ähnliche Mundaussparung **nicht** als festes Pac-Man-Gelb, sondern als Keil (Polygon-Cut via zweites Circle in Hintergrundfarbe ist verboten, weil es nicht transparent wäre). Stattdessen: Zeichne den Körper als Polygon-Fächer (36 Segmente) und lasse einen Mundwinkel von ±28° offen.
- Zwei kleine „Orbit“-Polygone (Dreiecke) bei 10 Uhr und 2 Uhr in Cyan, als CHAOS-Signet-Ersatz.
- Ein Auge: Kreis, dunkel, sitzt oberhalb der Mundmitte.

Der Fallback muss auf den ersten Blick als spielbarer Arcade-Kopf lesbar sein, auch ohne Firmenlogo.

### 1.3 Richtungs-Transformation (keine per-frame Vektorrotation)

Das Logo wird **einmal** in vier Richtungs-Surfaces gecacht.

Kanonische Annahme: Das Quelllogo „schaut“ nach **rechts** (positive X). Ist das falsch, korrigiert `LOGO_BASE_FACING = "right"` in `config.py` die Basis. Nur dieser eine Parameter darf gedreht werden, nicht die Gameplay-Logik.

| Richtung | Transformation aus Basis-Surface (facing right) |
|---|---|
| RIGHT | unverändert |
| LEFT | `pygame.transform.flip(base, True, False)` |
| UP | `pygame.transform.rotate(base, 90)` |
| DOWN | `pygame.transform.rotate(base, -90)` |

Regeln:

- `rotate` in Pygame ändert die Surface-Dimension. Nach jeder Rotation: zurück ins `size×size`-Quadrat zentrieren (`_fit_square(surf, size)`).
- Niemals `rotozoom` pro Frame.
- Niemals das SVG neu parsen, um eine Richtung zu erzeugen.
- Spiegelung für LEFT ist der Default, weil viele Logos Buchstaben enthalten: eine 180°-Rotation würde Schrift auf den Kopf stellen. Flip erhält die Lesbarkeit besser als `rotate(180)`.
- Wenn `LOGO_LEFT_MODE = "flip"` (Default) unlesbar ist (stark asymmetrisches Signet), darf auf `"rotate"` umgeschaltet werden — nur über Konstante, nicht hardcoded.

Zusätzlicher Cache: `FRIGHTENED` färbt eine Kopie des RIGHT-Frames per Pixel-Multiply in `#3B4CFF` (einmalig). Wird für den Spieler nicht genutzt, aber die gleiche Hilfsfunktion `tint_surface(surf, color)` wird für Geister-Flee-State verwendet.

### 1.4 Animations-Overlay (Logo bleibt erkennbar)

- Das Logo selbst pulsiert **nicht** in der Größe (keine Scale-Animation — teuer und unruhig).
- Mund-/Aktivitäts-Feedback: ein 2 px cyan Ring um das Tile, Alpha 80–160, sin-Pulse 2 Hz, nur im State `PLAYING` während Bewegung.
- Bei Stillstand: Ring aus, Logo statisch.

### 1.5 Fehler- und Logging-Vertrag

`LogoAsset.load` wirft **keine** Exception nach außen. Rückgabe ist immer eine gültige Surface. Intern:

```
[assets] SVG loaded via cairosvg: assets/logo.svg
[assets] SVG load failed (FileNotFoundError), using fallback geometry
[assets] cairosvg missing, pygame load failed, using fallback geometry
```

Logs gehen nach `stdout` (systemd/journal auf dem Pi).

### 1.6 Abhängigkeiten der Pipeline

```
cairosvg          # Python
cairocffi
cssselect2
tinycss2
defusedxml
pillow
```

Systemseitig auf Raspberry Pi OS:

```
libcairo2
libcairo2-dev
libgdk-pixbuf-2.0-0
libffi-dev
libxml2
libpango-1.0-0
shared-mime-info
```

`cairosvg` ist **optional zur Laufzeit**. Fehlt es, greift Stufe B/C. `requirements.txt` listet `cairosvg` trotzdem, `setup_pi5.sh` installiert die Systemlibs.

---

## 2. Game-Engine Architecture (Python / Pygame)

### 2.1 Hauptloop — unveränderliches Gerüst

```
init pygame, display, mixer (mixer failures ignorieren)
load config, assets, maze, highscores
state = START_SCREEN
last_input_ts = now
while running:
    dt = clock.tick(60) / 1000.0
    events = pygame.event.get()
    command = InputMap.poll(events, pygame.joystick)
    if command.activity:
        last_input_ts = now
    state.on_command(command)
    state.update(dt)
    if now - last_input_ts >= INACTIVITY_SECONDS:
        force_transition(START_SCREEN)  # und Attract vorbereiten
    state.draw(screen)
    pygame.display.flip()
```

`dt` in Sekunden, alle Bewegungen zeitbasiert (Pixel/Sekunde bzw. Tiles/Sekunde), niemals frame-count-basiert.

### 2.2 State-Machine

Klasse: `GameState` (ABC) mit `enter()`, `exit()`, `on_command(cmd)`, `update(dt)`, `draw(surf)`.

Konkrete States, **exakte Enum-Namen**:

```
class StateId(Enum):
    START_SCREEN = "START_SCREEN"
    ATTRACT_MODE = "ATTRACT_MODE"
    PLAYING = "PLAYING"
    GAME_OVER = "GAME_OVER"
```

`Game` hält `current: GameState` und `change_state(new_id: StateId)`. Jeder Wechsel ruft `exit()` dann `enter()` auf. Keine direkten Cross-Calls zwischen States.

#### 2.2.1 START_SCREEN

- Vollflächiger Dark-Background.
- Zentriert: das Firmenlogo in 160×160 (eigener Cache `logo_hero`, gleiche Pipeline, size=160).
- Titelzeile: `CHAOS PACMAN` in 64 px, Tracking weit, Farbe `#F4F1EA`.
- Unterzeile blinkend 1,2 Hz: `DRÜCKE START` (Gamepad Start/A/Any-Face oder Keyboard Enter/Space).
- Rechts oder unten: `HI-SCORE` + bester lokaler Wert, immer 6-stellig zero-padded.
- Kein Credit-System, kein Coin-Insert.
- Übergang nach `PLAYING` bei `command.start` oder `command.any_action`.
- Nach `ATTRACT_IDLE_SECONDS = 12` ohne Input automatisch nach `ATTRACT_MODE`.

#### 2.2.2 ATTRACT_MODE

- Spielt eine **deterministische Demo** auf dem echten Maze ab: Player + Geister laufen vorberechnete oder einfache Auto-Inputs.
- HUD zeigt `DEMO` statt Score-Interaktion.
- Jeder Input (`command.activity == True`) bricht sofort nach `START_SCREEN` ab — nicht direkt ins Spiel, damit der Besucher den Titel sieht und bewusst startet.
- Demo endet nach `ATTRACT_DURATION_SECONDS = 25` oder Player-Death in der Demo → zurück `START_SCREEN`.
- Attract darf Highscore **nicht** überschreiben.

#### 2.2.3 PLAYING

- Eine Runde, ein Leben-Modell für die Messe: **3 Leben**, Start mit 3.
- Score, Leben, Level im HUD (oben, 48 px Zeile, nicht über Maze).
- Pause existiert **nicht** (Kiosk).
- Tod → kurzes Freeze 1,4 s, Leben−1, Respawn Mitte/Starttile. Bei 0 Leben → `GAME_OVER`.
- Alle Dots gefressen → Level+1, Maze reset, Geister schneller (`GHOST_SPEED * (1 + 0.08 * (level-1))`, Cap 1.6×), Player-Speed Cap 1.25×.

#### 2.2.4 GAME_OVER

- Overlay: `GAME OVER`, finaler Score, Rang wenn Top-10.
- Speichert Score automatisch in `data/highscores.json` (kein Namenseintrag — Messefluss; Zeitstempel reicht).
- Zeigt 6 s lang das Overlay **oder** bis Start-Button.
- Danach immer `START_SCREEN`.
- Inaktivität von 30 s gilt auch hier und führt zu `START_SCREEN` (bereits durch globalen Timer abgedeckt).

### 2.3 Messe-Kiosk-Features

#### 2.3.1 Inaktivitäts-Timer

```
INACTIVITY_SECONDS = 30
ATTRACT_IDLE_SECONDS = 12
```

- „Aktivität“ = jede Richtung, jeder Button, jede Taste außer reinen Fenster-Events.
- Timer gilt in **allen** States.
- Bei Timeout aus `PLAYING` oder `GAME_OVER`: Runde verwerfen (Score nur speichern, wenn `GAME_OVER` bereits erreicht war; Abbruch aus `PLAYING` speichert **nicht**).
- Timeout setzt Joystick-Deadzone-Rauschen nicht als Aktivität. Analog-Stick unter `AXIS_DEADZONE = 0.45` ist keine Aktivität.

#### 2.3.2 Highscore-Speicher

Datei: `data/highscores.json`

Schema:

```json
{
  "updated_at": "ISO-8601",
  "entries": [
    {"score": 12340, "level": 2, "ts": "ISO-8601"}
  ]
}
```

Regeln:

- Maximal 10 Einträge, sortiert `score` desc, dann `ts` desc.
- Schreiben: temp-Datei `highscores.json.tmp` im selben Ordner, dann `os.replace` (atomar auf ext4).
- Lesefehler / JSON corrupt → leere Liste, Datei beim nächsten Write neu.
- `HighscoreStore.add(score, level)` ist idempotent pro GAME_OVER-Aufruf (State ruft genau einmal in `enter()`).
- Verzeichnis `data/` wird beim ersten Write erzeugt.

#### 2.3.3 Kiosk-Display

- `pygame.display.set_mode((0, 0), pygame.FULLSCREEN)` auf dem Pi.
- Env-Flag `CHAOS_WINDOWED=1` öffnet 1280×720 Fenster (Entwicklung am Mac/PC).
- Interne Render-Surface immer 1280×720, danach `smoothscale` auf das echte Fenster. HUD- und Maze-Koordinaten bleiben fest.
- Mauscursor: `pygame.mouse.set_visible(False)`.

#### 2.3.4 Operator-Hotkeys (nicht auf dem Startscreen erklären)

- `Q` + `Left-Shift`: sauberes Beenden (nur für Aufbau/Techniker).
- `F11`: Fullscreen toggle (Dev).
- `R` + `Left-Shift`: Highscores löschen.

### 2.4 Gamepad / Keyboard Event-Loop

Klasse `InputMap`. Ausgabe pro Frame: `Command`.

```
@dataclass(frozen=True)
class Command:
    dx: int          # -1, 0, +1  (gewünschte Rasterrichtung X)
    dy: int          # -1, 0, +1
    start: bool      # Start / Pause-Äquivalent / Bestätigen
    any_action: bool # Face-Button oder Enter/Space
    activity: bool   # irgendein Spielerimpuls inkl. Richtung
    quit_combo: bool # Operator-Quit
```

`dx/dy` sind **disjunkt**: niemals Diagonalen. Priorität:

1. D-Pad (HAT) wenn ≠ (0,0)
2. Analog-Stick, Achse 0/1, Schwelle `AXIS_DEADZONE = 0.45`; die Achse mit größerem Absolutwert gewinnt (kein Diagonal)
3. Tastatur Pfeile / WASD
4. sonst (0,0)

Letzte nicht-null Richtung wird als `queued_dir` im Player gehalten (Arcade-Klassik: Prefetch an Kreuzungen).

#### 2.4.1 8BitDo DIY Kit — verbindliches Mapping

Der 8BitDo DIY Kit erscheint unter Linux typischerweise als Joystick-Index 0, Name enthält `8BitDo` oder `Xbox` (X-Input-Modus) oder `Generic`. Das Mapping darf **nicht** am Gerätenamen scheitern.

| Aktion | Keyboard | Gamepad (pygame.joystick) |
|---|---|---|
| Hoch | `K_UP`, `K_w` | HAT 0 y=+1 **oder** Axis 1 < −DEADZONE |
| Runter | `K_DOWN`, `K_s` | HAT 0 y=−1 **oder** Axis 1 > +DEADZONE |
| Links | `K_LEFT`, `K_a` | HAT 0 x=−1 **oder** Axis 0 < −DEADZONE |
| Rechts | `K_RIGHT`, `K_d` | HAT 0 x=+1 **oder** Axis 0 > +DEADZONE |
| Start / Bestätigen | `K_RETURN`, `K_SPACE` | Button 0 (A), Button 1 (B), Button 7 (Start), Button 9 (manche Firmware) |
| Aktivität | jede der oben | jede der oben |

Implementierungsregeln:

- `pygame.joystick.init()`; alle Sticks öffnen (`Joystick(i).init()`).
- Hot-Plug: auf `JOYDEVICEADDED` / `JOYDEVICEREMOVED` neu enumerieren. Kein Crash bei Abziehen mitten im Spiel.
- HAT-Werte in Pygame: x ∈ {-1,0,1}, y ∈ {-1,0,1}. **Achtung:** y-Vorzeichen variiert je nach Treiber. Deshalb beide Interpretationen testen über `HAT_Y_INVERT = True` als Config-Default auf Pi (8BitDo oft invertierte Y-Achse am Analog, HAT meist korrekt). Analog-Y ist fast immer: oben = negativ.
- Buttons per **OR** über eine Menge `START_BUTTONS = {0, 1, 7, 9}` — nicht ein einzelner Index.
- `get_pressed()` für Keyboard **und** Event-Queue für `JOYBUTTONDOWN` (Buttons als Edge für `start`, Richtung als Level).
- Analog-Drift: Werte innerhalb der Deadzone sind 0. Kein `activity` bei Drift.

#### 2.4.2 Command-Semantik in States

| State | Richtung | Start/Action |
|---|---|---|
| START_SCREEN | ignoriert (zählt als activity → hält Attract auf) | → PLAYING |
| ATTRACT_MODE | activity → START_SCREEN | → START_SCREEN |
| PLAYING | queued direction | ignoriert |
| GAME_OVER | ignoriert (activity hält Timer) | → START_SCREEN |

### 2.5 Initialisierung und Robustheit

- `SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS=1` setzen vor `pygame.init()`.
- Audio: `try mixer.init except pygame.error: audio_enabled = False`.
- Font: `pygame.font.Font(None, size)` ist akzeptabel; wenn `/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf` existiert, diesen nutzen (bessere Lesbarkeit).
- Uncaught Exception im Loop: loggen, 2 s warten, State hart auf `START_SCREEN` (Kiosk darf nicht auf Traceback stehen bleiben). Optionaler Outer-Restart in `if __name__`.

---

## 3. Spielmechanik & KI

### 3.1 Maze — Grid-System

#### 3.1.1 Darstellung

Das Labyrinth ist ein **2D-Array von Tiles**, nicht Pixel-Geometrie.

```
class Tile(Enum):
    WALL = "#"
    EMPTY = " "
    DOT = "."
    POWER = "O"
    GATE = "-"      # Geisterhaus-Tür, Player kann nicht hindurch
    TUNNEL = "T"    # Wrap-around links/rechts
    SPAWN_P = "P"
    SPAWN_G = "G"   # Geisterhaus-Innen
```

Ein Level-Stringblock in `config.py` (28 Spalten × 31 Zeilen, klassisches Pac-Man-Seitenverhältnis, an 1280×720 angepasst):

- Maze-Pixelbreite: `28 * 32 = 896`
- Maze-Pixelhöhe: `31 * 32 = 992` → **zu hoch für 720**.

Deshalb: **angepasstes Messe-Maze** mit genau:

```
MAZE_COLS = 21
MAZE_ROWS = 17
TILE_SIZE = 32
MAZE_W = 672
MAZE_H = 544
```

Maze wird auf der 1280×720-Surface **zentriert** (Offset `((1280-672)//2, 80)`), HUD in den oberen 80 px, unterer Streifen 720−80−544 = 96 px für Branding `CHAOS` + Steuerungshinweis.

#### 3.1.2 Verbindliches Maze-Layout (ASCII)

Das Layout **muss** folgende Eigenschaften erfüllen:

- Geschlossener Außenrand aus `#` außer genau einem `T`-Paar in der mittleren Zeile links/rechts (Tunnel).
- Zusammenhängende Gänge; keine unerreichbaren Dots.
- Geisterhaus 5×3 im Zentrum, Tür `-` nach oben.
- Player-Spawn `P` unterhalb des Hauses, zentriert.
- Genau **4** Power-Pellets `O` in den vier Quadranten, nicht in Ecken hinter Sackgassen ohne Flucht.
- Dot-Anzahl nach dem Parsen ≥ 80 (sonst ist das Level zu leer für Messe-Feedback).

Beispiel-Skeleton (21×17) — die Implementierung darf kosmetisch variieren, muss aber denselben Vertrag erfüllen:

```
#####################
#.........#.........#
#O##.###.#.###.##O#.#
#...................#
#.##.#.#####.#.##.#.#
#....#...#...#....#.#
####.###.#.###.######
T   #.# GGG #.#    T
####.#.-----#.#.#####
#....#...P...#....#.#
#.##.#.#####.#.##.#.#
#...................#
#O##.###.#.###.##O#.#
#.........#.........#
#####################
```

(Zeilen auf exakt 21 Zeichen und 17 Zeilen bringen; das Skeleton oben ist konzeptionell. Die Implementierung liefert ein **valides, ausgezähltes** 21×17-Feld.)

#### 3.1.3 Kollision und Bewegung

Entitäten besitzen:

- `tile: tuple[int, int]` — aktuelle Zelle
- `pixel: pygame.Vector2` — Zentrum in Maze-Pixeln (nicht Screen)
- `dir: tuple[int, int]` — aktuelle Bewegungsrichtung
- `queued: tuple[int, int]` — Wunschrichtung
- `speed: float` — Tiles pro Sekunde (Player Base `7.0`, Ghost Base `6.2`)

Bewegungsregeln (Arcade-korrekt, vereinfacht):

1. Bewegung nur entlang der Grid-Achsen.
2. Richtungswechsel 180° (Reverse) ist **sofort** erlaubt.
3. 90°-Wechsel nur, wenn die Entity **im Zentrum der Zelle** ist (`distance_to(tile_center) <= TURN_EPSILON`, `TURN_EPSILON = 3.0` px) **und** das Ziel-Tile begehbar ist.
4. Ist die Wunschrichtung noch nicht legal, bleibt `queued` erhalten, die Entity läuft weiter geradeaus, bis die Kreuzung passt oder eine Wand stoppt.
5. Wand: Entity rastet auf Tile-Zentrum ein, `dir` bleibt, Bewegung 0 bis neue legale Queue.
6. Tunnel `T`: Verlassen über linken Rand → Erscheinen rechter `T` und umgekehrt. `pixel.x` wrap. Geister dürfen Tunnel nutzen, aber ihre Speed im Tunnel `* 0.6` (klassische Lesbarkeit).

Begehbarkeit:

| Tile | Player | Ghost |
|---|---|---|
| WALL `#` | nein | nein |
| GATE `-` | nein | ja, nur beim Verlassen des Hauses |
| SPAWN_G | nein | ja |
| DOT/EMPTY/POWER/P/T | ja | ja |

#### 3.1.4 Dots und Scoring

| Event | Punkte |
|---|---|
| Dot | 10 |
| Power-Pellet | 50 |
| Geist 1/2/3/4 in derselben Frightened-Kette | 200 / 400 / 800 / 1600 |
| Level-Clear Bonus | 500 |

- Dot wird beim Betreten der Zelle gegessen (`tile` wechselt oder Distanz Zentrum < 6 px).
- Power-Pellet setzt alle Geister, die nicht bereits `EATEN` sind, auf `FRIGHTENED` für `FRIGHTENED_SECONDS = 6.0` (Level 1), −0,5 s je Level, Minimum 2,0 s.
- Frightened: Geister blau `#3B4CFF`, Speed `* 0.55`, KI = zufällige legale Richtung an jeder Kreuzung (kein Reverse außer beim Eintritt in FRIGHTENED — einmal erzwungenes Reverse).
- Gegessen: Geist → `EATEN`, Augen-only Draw, Speed `* 1.6`, Ziel = Hausmitte, dort Respawn nach 1,0 s als `LEAVE`.

Gewinn der Runde: `remaining_dots == 0`.

### 3.2 Spieler

Klasse `Player`.

- Start: Tile `P`, Facing RIGHT, queued RIGHT.
- Unverwundbar `INVULN_SECONDS = 2.0` nach Respawn (Blink 8 Hz). In der Zeit keine Geist-Kollision.
- Kollision mit Geist: Kreis-Kreis, Radius je `TILE_SIZE * 0.35`. Nur wenn Geist in `CHASE` oder `SCATTER`. `FRIGHTENED` → essen. `EATEN`/`LEAVE`/`HOUSE` → keine Kollision.
- Zeichnung: `LogoAsset.frames[facing]` zentriert auf `pixel + maze_offset`.
- Kein Extra-Leben.

### 3.3 Geister-KI (4 Geister)

Klassen: `Ghost`, Enum `GhostId {BLINKY, PINKY, INKY, CLYDE}`, Enum `GhostMode {HOUSE, LEAVE, SCATTER, CHASE, FRIGHTENED, EATEN}`.

#### 3.3.1 Gemeinsame Navigation

An jedem Tile-Zentrum wählt der Geist **genau eine** legale Nachbarzelle. Reverse ist verboten, außer:

- Mode-Wechsel nach FRIGHTENED (einmal),
- Mode-Wechsel SCATTER↔CHASE (einmal),
- EATEN (kürzester Weg, Reverse erlaubt).

Zielwahl: `target_tile: tuple[int,int]`. Unter allen legalen Nachbarn (ohne Reverse) wird der mit minimaler **euklidischer** Distanz zum Target gewählt. Bei Gleichstand feste Priorität: **UP, LEFT, DOWN, RIGHT** (Arcade-Kanon).

Scatter-Ziele (Ecken, können außerhalb liegen):

| Geist | Scatter-Tile |
|---|---|
| BLINKY | `(MAZE_COLS-1, 0)` |
| PINKY | `(0, 0)` |
| INKY | `(MAZE_COLS-1, MAZE_ROWS-1)` |
| CLYDE | `(0, MAZE_ROWS-1)` |

Globaler Mode-Timer (nicht frightened/eaten):

```
Level 1: SCATTER 7s → CHASE 20s → SCATTER 7s → CHASE 20s → SCATTER 5s → CHASE ∞
Ab Level 3: SCATTER 5s → CHASE 20s → SCATTER 5s → CHASE ∞
```

Timer pausiert während FRIGHTENED.

#### 3.3.2 Persönlichkeiten (Chase-Targets)

**BLINKY (rot, aggressiv):** Target = aktuelles Player-Tile. Immer direkte Jagd. Wenn remaining_dots < 20: Speed `* 1.1` („Elroy“-light).

**PINKY (pink, Hinterhalt):** Target = 4 Tiles **vor** dem Spieler in dessen Facing. Facing UP nutzt den historischen Overflow **nicht** (kein +4x/−4y-Bug). Nur 4 Tiles in Facing-Richtung, geclampt an Maze-Rand.

**INKY (cyan, Flanken):** Sei `pivot` = 2 Tiles vor dem Spieler. Sei `blinky` = Blinkys Tile. Target = `pivot + (pivot - blinky)` (Punktspiegelung). Ergebnis darf außerhalb des Mazes liegen.

**CLYDE (orange, feige):** Wenn Distanz zu Player > 8 Tiles: Target = Player-Tile (wie Blinky). Sonst: Scatter-Ecke. Distanz euklidisch in Tiles.

#### 3.3.3 House / Leave

- Alle Geister starten im Haus (`G`-Tiles).
- Leave-Staffelung nach Rundenstart oder Respawn: Blinky 0,2 s, Pinky 0,8 s, Inky 2,4 s, Clyde 4,0 s. Ab Level 2 jeweils −0,3 s, Minimum 0,1 / 0,3 / 0,8 / 1,5 s.
- `LEAVE`: Target = Tile direkt über der Gate. Bewegung darf GATE kreuzen. Nach Verlassen: aktueller Global-Mode.
- Eintritt nur als `EATEN`.

#### 3.3.4 Zeichnung der Geister

Keine SVG-Geister. Reine Pygame-Primitives, 32×32:

- Körper: Kreis oben + Rechteck unten, Farbe der Id.
- Zwei Augen (Weiß + Pupille in Bewegungsrichtung).
- Rocksaum: 3 Halbkreise am unteren Rand.
- FRIGHTENED: Körper blau, Augen weiß, nach 2 s Restzeit Blink Weiß/Blau 8 Hz.
- EATEN: nur Augen.

### 3.4 Kamera / Rendering-Order

1. Clear Backbuffer `#0B0D10`
2. HUD
3. Maze-Wände
4. Dots / Power-Pellets (Pellets skalieren mit `1 + 0.15*sin(t*8)`)
5. Geister (EATEN zuletzt über anderen, damit Augen sichtbar)
6. Player
7. State-Overlays (Start / Attract-Banner / Game Over)
8. Optionaler Scanline-Overlay 5 % Alpha (ein `src_alpha` Streifen-Surface, gecacht) — darf auf Pi weggelassen werden, wenn FPS < 50, gemessen über gleitenden 60-Frame-Schnitt. Config `ENABLE_SCANLINES = True`.

### 3.5 Audio (optional, nie blockierend)

Wenn Mixer verfügbar:

- Waka: kurzer Square-Click beim Dot, nicht bei jedem Frame.
- Power: tieferer Ton.
- Death: absteigende Folge.
- Start: aufsteigender Arpeggio.

Alles synthetisch mit `pygame.sndarray` oder stummschaltbar. **Keine** WAV-Dateien Pflicht. Fehlt Audio, bleibt das Spiel identisch spielbar.

---

## 4. Implementierungsauftrag (Schritt 2 — verbindlich)

Wenn dieses Dokument ausgeführt wird, gilt:

1. Liefere lauffähigen Code gemäß Dateistruktur in 0.5. Bündelung in `main.py` ist erlaubt, wenn alle genannten Klassen existieren.
2. Liefere `requirements.txt` und `setup_pi5.sh` mit exakten apt- und pip-Befehlen für Raspberry Pi 5 / Bookworm.
3. Liefere eine kurze `README.md` mit Startbefehl `python3 main.py` und dem Hinweis `CHAOS_WINDOWED=1` für Entwicklung.
4. Das Spiel muss **ohne** `logo.svg` starten und den Fallback zeichnen.
5. Liegt `assets/logo.svg` vor, muss es automatisch als Spielerfigur in vier Richtungen erscheinen.
6. Tastatur allein muss das ganze Spiel bedienbar machen (CI/Dev ohne Stick).
7. Kein Netzwerk, kein pip-Download zur Laufzeit, keine Telemetrie.
8. Kommentare im Code auf Deutsch oder Englisch, aber konsistent; öffentliche Bezeichner Englisch wie in diesem Dokument.
9. Keine Platzhalter (`TODO`, `pass` in Gameplay-Pfaden, `NotImplementedError`).
10. Nach der Implementierung muss ein Entwickler auf dem Pi genau diese Sequenz ausführen können:

```
chmod +x setup_pi5.sh
./setup_pi5.sh
python3 main.py
```

---

## 5. Abnahmekriterien (Definition of Done)

- [ ] Start auf Pi 5 und auf Desktop (windowed) ohne Crash, auch ohne SVG und ohne Gamepad.
- [ ] Logo-Pipeline: cairosvg → pygame → Fallback, nachweisbar über stdout-Logs.
- [ ] Richtungswechsel ändert Logo-Orientierung (Flip/Rotate-Cache).
- [ ] 8BitDo D-Pad, Analog (Deadzone), A/Start und Keyboard parallel.
- [ ] 30-s-Inaktivität aus PLAYING kehrt zu START_SCREEN zurück ohne Highscore-Write.
- [ ] 12 s auf START_SCREEN startet ATTRACT_MODE; Input zurück zum Titel.
- [ ] Highscores überleben Prozess-Neustart (`data/highscores.json`).
- [ ] Vier Geister mit unterscheidbarem Chase-Verhalten, Frightened, Eaten-Return.
- [ ] Dots essen, Power-Pellets, Level-Clear, 3 Leben, GAME_OVER-Overlay.
- [ ] Tunnel-Wrap funktioniert für Player und Geister.
- [ ] Fullscreen-Kiosk, Cursor unsichtbar, Operator-Quit Shift+Q.
- [ ] Stabil ≥ 50 FPS auf Pi 5 bei 1280×720 intern.

---

## 6. Self-Check vor dem Commit der Implementierung

Der implementierende Agent prüft vor Abschluss:

1. Existieren alle in §0.5 genannten Dateien **oder** deren vollständige Äquivalente in `main.py`?
2. Gibt es genau eine Quelle für Konstanten (`config.py` oder `CONFIG`-Block)?
3. Wird `logo.svg` niemals pro Frame gerastert?
4. Sind Diagonalen unmöglich?
5. Kann das Spiel 2 Minuten ohne Input im Attract/Start-Zyklus allein laufen?
6. Ist `data/highscores.json` gitignored?

Ende des Master-Prompts. Dieses Dokument ist die einzige Wahrheitsquelle für die Code-Generierung.
