# CHAOS Arcade — Master-Prompt / System-Instruction Set

**Dokumenttyp:** Pflichtenheft + Self-Instruction Set für Code-Generierung  
**Produktname (UI):** `CHAOS ARCADE`  
**Repo-/Ordnername:** `CHAOS_PacMan` (unverändert; kein Rename-Zwang)  
**Zielplattform:** Raspberry Pi 5 (64-bit Raspberry Pi OS)  
**Stack:** Python 3.11+ / Pygame 2  
**Eingabe:** 8BitDo DIY Kit (Bluetooth Arcade-Stick) + Tastatur-Pfeiltasten  
**Spieler-Asset:** `assets/logo.svg` (Firmenlogo, Vektor) — **in jedem Spiel** die Spielfigur  
**Betriebsart:** Unbeaufsichtigtes Messe-Kiosk am digitalen Pult  

**Spielkatalog (verbindlich, genau diese fünf, in dieser Reihenfolge):**

| `GameId` | UI-Titel | Genre-Vorbild | Kernschleife (Messe, 30–90 s) |
|---|---|---|---|
| `PACMAN` | PAC-MAN | Pac-Man | Labyrinth, Dots, 4 Geister |
| `DONKEY_KONG` | DONKEY KONG | Donkey Kong | Plattformen, Leitern, Fässer, Sprung |
| `SNAKE` | SNAKE | Snake | Wachsen, nicht selbst treffen |
| `BUBBLE_SHOT` | BUBBLE SHOT | Puzzle Bobble / Bubble Shooter | Zielen, schießen, 3er-Match |
| `FROGGER` | FROGGER | Frogger | Straßen/Fluss queren, 5 Ziele |

Dieses Dokument ist verbindlich. CHAOS Arcade ist **kein** reiner Pac-Man-Klon. Pac-Man ist das **erste** Spiel im Kabinett, nicht das einzige. Jede nachfolgende Implementierung muss sich **wortgetreu** an diese Vorgaben halten. Abweichungen sind nur zulässig, wenn sie einen Laufzeitfehler auf dem Raspberry Pi 5 verhindern — und müssen dann im Code kommentiert werden.

Rechtlicher Rahmen: Es werden **keine** originalen ROM-Assets, Sprites, Melodien oder Markenzeichen Dritter eingebettet. Mechanik und Feeling dürfen anklingen; visuelle Identität ist ausschließlich CHAOS (Logo + Neon-Palette).

---

## 0. Nicht verhandelbare Leitplanken

### 0.1 Betriebsziel

CHAOS Arcade ist ein **Multi-Game-Mitmach-Kabinett**. Ein Messebesucher greift zum Arcade-Stick, wählt in ≤ 5 Sekunden ein Spiel, spielt eine kurze Runde, sieht den Score, und das Gerät kehrt selbstständig zur Spielauswahl zurück.

- Es gibt **kein** Dateimenü, **kein** OS-UI, **kein** Beenden über sichtbare Buttons.
- Vollbild-Verlassen nur über verstecktes Operator-Hotkey (siehe 2.5).
- Jedes der fünf Spiele muss **allein mit Stick + einem Action-Button** bedienbar sein.
- Typische Runde: **30–90 Sekunden**. Kein Spiel darf eine Einarbeitungszeit > 3 Sekunden brauchen.
- Das Firmenlogo ist in **allen** Spielen der Avatar (Mund/Kopf, Kletterer, Schlangenkopf, Kanone/Kugel, Springer).

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
- Pro Frame maximal die aktive Spielszene plus HUD. Inaktive Games werden nicht simuliert (außer Attract-Demo des aktuellen Slots).
- Keine Blocking-I/O im Game-Loop. Highscore-Schreiben erfolgt atomar und kurz.
- Ziel: stabil ≥ 50 FPS auf Pi 5 bei 1280×720, **in jedem** der fünf Spiele.

### 0.4 Code-Qualität

- Klare Modulstruktur (siehe 0.5). `main.py` ist der Einstieg.
- Die erste lauffähige Version darf Module bündeln, **muss** aber die genannten Klassen-/Funktionsnamen verwenden.
- Typ-Hints an allen öffentlichen Funktionen und Klassenmethoden.
- Keine Magic Numbers ohne benannte Konstanten (`config.py` + optional `games/<id>/constants.py`).
- Keine Netzwerkzugriffe, keine Telemetrie.
- UTF-8, Linux-Zeilenenden.
- Lauffähig **ohne** `logo.svg` (Fallback-Renderer ist Pflicht).
- Jedes Spiel implementiert dasselbe `GameMode`-Protokoll. Keine Sonderwege für Pac-Man.

### 0.5 Verbindliche Dateistruktur

```
CHAOS_PacMan/
├── main.py                 # Einstieg + Shell-Loop
├── config.py               # Shared Konstanten, Farben, Timing, Display
├── input_map.py            # Keyboard + Gamepad-Mapping
├── assets_loader.py        # SVG-Pipeline + Fallback-Logo
├── states.py               # Shell-States: SELECT, ATTRACT, PLAYING, GAME_OVER
├── highscore.py            # JSON Persistenz, getrennt pro GameId
├── game_mode.py            # ABC GameMode
├── games/
│   ├── pacman/
│   │   ├── maze.py
│   │   ├── player.py
│   │   ├── ghosts.py
│   │   └── mode.py         # PacmanMode(GameMode)
│   ├── donkey_kong/
│   │   ├── stage.py
│   │   ├── barrels.py
│   │   └── mode.py
│   ├── snake/
│   │   └── mode.py
│   ├── bubble_shot/
│   │   ├── grid.py
│   │   └── mode.py
│   └── frogger/
│       ├── lanes.py
│       └── mode.py
├── attract.py              # Demo-Steuerung, rotiert durch alle Games
├── assets/
│   └── logo.svg            # Firmenlogo (kann fehlen)
├── data/
│   └── highscores.json     # wird zur Laufzeit erzeugt
├── requirements.txt
├── setup_pi5.sh
├── MASTER_PROMPT.md
└── README.md
```

Die erste Auslieferung darf alles in `main.py` vereinen, **muss** aber `GameId`, `GameMode` und die fünf Mode-Klassen (`PacmanMode`, `DonkeyKongMode`, `SnakeMode`, `BubbleShotMode`, `FroggerMode`) namentlich enthalten.

### 0.6 Visuelle Identität (Arcade / CHAOS)

Shared:

- Hintergrund: tiefes Anthrazit `#0B0D10`.
- HUD: monospace, hoher Kontrast, große Zahlen (Lesbarkeit ab 1,5 m).
- Akzent: neon-cyan `#2DE2E6`, Warmweiß `#F4F1EA`, Bernstein `#FFB703`.
- Gefahr: `#FF3B3B`. Support: `#FF7AD9`, `#3BD1FF`, `#FF9F1C`.
- Kein Comic-Pac-Man-, kein Nintendo-, kein Konami-Sprite. Der Spieler **ist** das Firmenlogo.

Akzente pro Spiel (nur Level-Geometrie, nicht das Logo):

| Game | Primärakzent | Level-Look |
|---|---|---|
| PACMAN | `#2DE2E6` | Neon-Maze, dunkler Innenfill `#12161C` |
| DONKEY_KONG | `#FF9F1C` | Nieten-Träger, Leitern cyan, Fässer rot |
| SNAKE | `#2DE2E6` | Dunkelgrid, Food bernstein |
| BUBBLE_SHOT | `#3BD1FF` | Kugelfarben aus der CHAOS-Palette |
| FROGGER | `#3BD1FF` / `#FF3B3B` | Straße dunkel, Wasser cyan-dunkel, Ziele bernstein |

---

## 1. Asset-Pipeline & SVG-Rendering

### 1.1 Quelle und Verträge

- Primärpfad: `assets/logo.svg`.
- Das SVG gilt als **quadratisch normiert**. Nicht-quadratische ViewBox: proportional fitten, zentrieren, niemals strecken.
- Mehrere Rastergrößen, **einmal** beim Boot cachen:

| Cache-Key | Größe | Verwendung |
|---|---|---|
| `logo_hero` | 160 | SELECT / Titel |
| `logo_tile` | `TILE_SIZE - 4` (Default 28) | Pac-Man, Snake-Kopf, Frogger |
| `logo_dk` | 36 | Donkey-Kong-Kletterer |
| `logo_cannon` | 48 | Bubble-Shot-Kanone |
| `logo_bubble` | 28 | Bubble-Shot-Kugel (getintet) |
| `logo_snake_body` | 24 | Snake-Körper (getintet, 70 % Alpha) |

`TILE_SIZE = 32` bleibt die Shared-Grid-Basis. Einzelne Games dürfen eigene Zellengrößen nutzen, beziehen sie aber aus `config.py`.

### 1.2 Ladestrategie (verbindliche Reihenfolge)

Klasse `LogoAsset`. Methode: `LogoAsset.load(path: Path, size: int) -> pygame.Surface`.

**Stufe A — cairosvg (bevorzugt auf Pi 5):**

```
SVG-Bytes → cairosvg.svg2png(bytestring=..., output_width=size*2, output_height=size*2)
         → PNG-Bytes → pygame.image.load(BytesIO(...)).convert_alpha()
         → smoothscale auf (size, size)
```

Zusätzlich quadratisch zentrieren:

1. Lade Surface.
2. `scale = size / max(w, h)`.
3. Proportional skalieren.
4. Auf transparente `size×size`-Surface zentriert blitten.

**Stufe B — pygame / SDL_image**, bei Exception weiter zu Stufe C.

**Stufe C — geometrischer Fallback** `render_fallback_logo(size)`:

- Kreis-Körper, Radius `size * 0.46`, Fill `#F4F1EA`, Outline `#2DE2E6`.
- Polygon-Fächer (36 Segmente), Mundwinkel ±28° offen.
- Zwei Orbit-Dreiecke (10 Uhr / 2 Uhr) in Cyan.
- Ein Auge oberhalb der Mundmitte.

`LogoAsset.load` wirft **keine** Exception nach außen.

### 1.3 Richtungs-Transformation

Einmal vier Richtungs-Surfaces pro Größe cachen. Basis: Logo schaut nach **rechts**. Korrektur nur über `LOGO_BASE_FACING`.

| Richtung | Transformation |
|---|---|
| RIGHT | unverändert |
| LEFT | `flip(base, True, False)` Default (`LOGO_LEFT_MODE = "flip"`) |
| UP | `rotate(base, 90)` + `_fit_square` |
| DOWN | `rotate(base, -90)` + `_fit_square` |

- Niemals `rotozoom` pro Frame, niemals SVG neu parsen.
- `tint_surface(surf, color)` einmalig für Snake-Körper, Frightened-Geister, Bubble-Farben.

### 1.4 Nutzungsregeln pro Spiel

| Game | Logo-Nutzung |
|---|---|
| PACMAN | `logo_tile` + Facing-Cache, Cyan-Ring nur bei Bewegung |
| DONKEY_KONG | `logo_dk`, Facing LEFT/RIGHT; UP nur auf Leiter (kein DOWN-Flip auf den Kopf — auf Leitern Facing unverändert oder leicht 0°) |
| SNAKE | Kopf = `logo_tile[facing]`; Körper = `logo_snake_body` getintet `#2DE2E6` |
| BUBBLE_SHOT | Kanone = `logo_cannon` rotiert auf **diskrete Winkelschritte** (gecachte 2°-Raster-Surfaces, 0…180° bzw. −80…+80); fliegende Kugel = `logo_bubble` getintet in Schussfarbe |
| FROGGER | `logo_tile[facing]`; Idle schaut UP |

Bubble-Shot-Rotation: Winkel-Cache beim Start in 2°-Schritten, **kein** per-frame `rotozoom` auf das SVG.

### 1.5 Logging

```
[assets] SVG loaded via cairosvg: assets/logo.svg
[assets] SVG load failed (...), using fallback geometry
```

### 1.6 Abhängigkeiten

Python: `cairosvg`, `cairocffi`, `cssselect2`, `tinycss2`, `defusedxml`, `pillow`, `pygame`.  
System (Pi): `libcairo2`, `libcairo2-dev`, `libgdk-pixbuf-2.0-0`, `libffi-dev`, `libxml2`, `libpango-1.0-0`, `shared-mime-info`.  
`cairosvg` optional zur Laufzeit; Fallback ist Pflicht.

---

## 2. Game-Engine Architecture (Python / Pygame)

### 2.1 Hauptloop — Shell, nicht Spiel

```
init pygame, display, mixer (mixer failures ignorieren)
load config, LogoAsset-Caches, HighscoreStore
registry = {
    PACMAN: PacmanMode,
    DONKEY_KONG: DonkeyKongMode,
    SNAKE: SnakeMode,
    BUBBLE_SHOT: BubbleShotMode,
    FROGGER: FroggerMode,
}
state = GAME_SELECT          # nicht mehr direkt PACMAN
selected = GameId.PACMAN
last_input_ts = now
while running:
    dt = clock.tick(60) / 1000.0
    events = pygame.event.get()
    command = InputMap.poll(events)
    if command.activity:
        last_input_ts = now
    state.on_command(command)
    state.update(dt)
    if now - last_input_ts >= INACTIVITY_SECONDS:
        force_transition(GAME_SELECT)
    state.draw(screen)
    pygame.display.flip()
```

Nur das **aktive** `GameMode` erhält `update`/`draw`. `dt` in Sekunden, zeitbasiert.

### 2.2 State-Machine (Shell)

```
class StateId(Enum):
    GAME_SELECT = "GAME_SELECT"
    ATTRACT_MODE = "ATTRACT_MODE"
    PLAYING = "PLAYING"
    GAME_OVER = "GAME_OVER"
```

`START_SCREEN` entfällt. Der Titel sitzt in `GAME_SELECT`.

`GameState`: `enter()`, `exit()`, `on_command(cmd)`, `update(dt)`, `draw(surf)`.  
`Game.change_state(new_id)` ruft `exit()` dann `enter()`.

#### 2.2.1 GAME_SELECT

- Oben: Logo 160 px + Titel `CHAOS ARCADE`.
- Mitte: **horizontale Carousel** der fünf Spiele. Aktives Spiel größer (Scale 1.0), Nachbarn 0.72, dimmed.
- Unter dem Slot: UI-Titel + eine Zeile Mechanik (`ISS DASS LABYRINTH` etc. — kurz, deutsch, max. 28 Zeichen).
- Unten: `HI-SCORE` des **selektierten** Spiels, 6-stellig; blinkend `◀ WÄHLEN   START SPIELEN ▶`.
- Links/Rechts bzw. Stick X wechselt `selected` (wrap: Pac-Man ↔ Frogger).
- `command.start` oder `command.any_action` → `PLAYING` mit `registry[selected].reset()`.
- Nach `ATTRACT_IDLE_SECONDS = 12` ohne Input → `ATTRACT_MODE`.
- Select-Wechsel ist `activity` und hält den Attract-Timer.

Carousel-Reihenfolge fest: Pac-Man, Donkey Kong, Snake, Bubble Shot, Frogger.

#### 2.2.2 ATTRACT_MODE

- Spielt eine **deterministische Demo** des aktuell (oder zuletzt) selektierten Spiels, dann rotiert alle `ATTRACT_ROTATE_SECONDS = 8` zum nächsten `GameId`.
- HUD: `DEMO` + Spielname.
- Jeder Input → sofort `GAME_SELECT` (nicht direkt ins Spiel).
- Attract schreibt **keine** Highscores und verbraucht keine Leben persistent.
- Gesamtdauer einer Attract-Session max. 40 s, danach zurück `GAME_SELECT` (Idle-Loop: Select 12 s → Attract → Select).

#### 2.2.3 PLAYING

- Instanziiert genau ein `GameMode`.
- HUD oben 80 px: Spielname, Score, Leben/Versuche, Level.
- Pause existiert **nicht**.
- `GameMode` signalisiert Ende über `Result.GAME_OVER` oder `Result.QUIT_TO_SELECT` (letzteres nur durch Inaktivität der Shell).
- Leben, Tempo, Level-Steigerung: **pro Spiel** in §3.x, nicht global identisch.

#### 2.2.4 GAME_OVER

- Overlay: Spielname, `GAME OVER`, Score, Rang in der **spieleigenen** Top-10.
- Speichert genau einmal in `enter()` via `HighscoreStore.add(game_id, score, level)`.
- 6 s oder Start-Button → `GAME_SELECT` (Selection bleibt auf dem gerade gespielten Game).

### 2.3 Messe-Kiosk-Features

#### 2.3.1 Inaktivitäts-Timer

```
INACTIVITY_SECONDS = 30
ATTRACT_IDLE_SECONDS = 12
ATTRACT_ROTATE_SECONDS = 8
```

- Aktivität = Richtung, Action, Start. Analog unter `AXIS_DEADZONE = 0.45` zählt nicht.
- Timeout in `PLAYING`/`GAME_OVER` → `GAME_SELECT`. Score aus `PLAYING` wird **nicht** gespeichert; aus `GAME_OVER` bereits gespeichert.

#### 2.3.2 Highscore-Speicher

Datei: `data/highscores.json`

```json
{
  "updated_at": "ISO-8601",
  "games": {
    "PACMAN": [{"score": 12340, "level": 2, "ts": "ISO-8601"}],
    "DONKEY_KONG": [],
    "SNAKE": [],
    "BUBBLE_SHOT": [],
    "FROGGER": []
  }
}
```

- Pro `GameId` maximal 10 Einträge, sortiert `score` desc, dann `ts` desc.
- Atomar: `highscores.json.tmp` + `os.replace`.
- Corrupt → leere Listen für alle fünf Keys, Rebuild beim Write.
- Altes Schema ohne `games`-Map (nur `entries`) einmalig nach `PACMAN` migrieren.
- `data/` wird beim ersten Write erzeugt.

#### 2.3.3 Kiosk-Display

- Pi: `set_mode((0, 0), FULLSCREEN)`.
- Dev: `CHAOS_WINDOWED=1` → 1280×720-Fenster.
- Interne Surface immer 1280×720, danach `smoothscale` aufs Fenster.
- `pygame.mouse.set_visible(False)`.

#### 2.3.4 Operator-Hotkeys

- `Q` + `Left-Shift`: Beenden.
- `F11`: Fullscreen toggle (Dev).
- `R` + `Left-Shift`: Highscores **aller** Spiele löschen.
- `1`…`5`: im Select-Screen Direktwahl (Dev): Pac-Man … Frogger.

### 2.4 Gamepad / Keyboard Event-Loop

```
@dataclass(frozen=True)
class Command:
    dx: int              # -1, 0, +1
    dy: int              # -1, 0, +1
    start: bool
    action: bool         # Edge: A / Space — Sprung, Schuss, Bestätigen
    action_held: bool    # Level: gehalten (für optionales Charging; Default ungenutzt)
    any_action: bool
    activity: bool
    quit_combo: bool
```

`dx/dy` disjunkt, keine Diagonalen. Priorität: D-Pad → Analog (größere Achse) → Tastatur → (0,0).

| Aktion | Keyboard | Gamepad |
|---|---|---|
| Hoch | `K_UP`, `K_w` | HAT y=+1 oder Axis 1 < −DEADZONE |
| Runter | `K_DOWN`, `K_s` | HAT y=−1 oder Axis 1 > +DEADZONE |
| Links | `K_LEFT`, `K_a` | HAT x=−1 oder Axis 0 < −DEADZONE |
| Rechts | `K_RIGHT`, `K_d` | HAT x=+1 oder Axis 0 > +DEADZONE |
| Action / Sprung / Schuss | `K_SPACE`, `K_LCTRL` | Button 0 (A), Button 1 (B) |
| Start / Bestätigen | `K_RETURN` | Button 7 / 9 (Start) **oder** Action, wenn der State Action als Start akzeptiert |
| Aktivität | jede der oben | jede der oben |

- Joystick-Hot-Plug ohne Crash.
- `HAT_Y_INVERT = True` als Pi-Default.
- `START_BUTTONS = {0, 1, 7, 9}` für Start in SELECT/GAME_OVER.
- `action` ist **Edge** (down in diesem Frame), sonst feuert Bubble Shot Dauerfeuer.

#### 2.4.1 Command-Semantik in der Shell

| State | Richtung | Action / Start |
|---|---|---|
| GAME_SELECT | wechselt Slot | → PLAYING |
| ATTRACT_MODE | → GAME_SELECT | → GAME_SELECT |
| PLAYING | an `GameMode` | an `GameMode` (`start` ignorieren) |
| GAME_OVER | activity hält Timer | → GAME_SELECT |

#### 2.4.2 Command-Semantik in den Spielen

| Game | Richtung | Action |
|---|---|---|
| PACMAN | queued Grid-Richtung | ignoriert |
| DONKEY_KONG | L/R laufen, U/D Leiter | Sprung (Edge) |
| SNAKE | queued Richtung, kein 180° in sich selbst | ignoriert |
| BUBBLE_SHOT | L/R dreht Kanone, U/D grob (größerer Winkelschritt) | Schuss (Edge) |
| FROGGER | ein Rasterschritt pro Tastendruck (Edge, nicht gehalten) | ignoriert (optional: Action = Hop nach oben) |

### 2.5 Robustheit

- `SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS=1` vor `pygame.init()`.
- Mixer-Fehler → `audio_enabled = False`.
- Font: DejaVu Sans Mono Bold falls vorhanden, sonst `Font(None, size)`.
- Uncaught Exception: loggen, 2 s warten, hart `GAME_SELECT`. Ein Game-Crash darf die anderen vier nicht töten — `GameMode.update` in try/except der Shell.

### 2.6 GameMode-Protokoll

```
class Result(Enum):
    CONTINUE = "CONTINUE"
    GAME_OVER = "GAME_OVER"

class GameMode(ABC):
    id: GameId
    def reset(self) -> None: ...
    def on_command(self, cmd: Command) -> None: ...
    def update(self, dt: float) -> Result: ...
    def draw(self, surf: pygame.Surface) -> None: ...
    def score(self) -> int: ...
    def level(self) -> int: ...
    def lives(self) -> int: ...
    def attract_tick(self, dt: float) -> None: ...   # Autoplay, keine Scores
```

---

## 3. Spielmechanik

Gemeinsam:

- Interne Szene unter dem 80-px-HUD, optional 96-px-Fußzeile mit `CHAOS` + Kurzsteuerung.
- 3 Leben, sofern das Spiel Leben hat (Snake: 1 Leben / Sofort-Out, dann GAME_OVER — siehe 3.C).
- Level-Steigerung erhöht Tempo oder Dichte, nie die Steuerung umbauen.

---

### 3.A PACMAN

Entspricht dem bisherigen Pac-Man-Vertrag. Kurzfassung der bindenden Regeln; Implementierung muss sie vollständig erfüllen.

#### 3.A.1 Grid

```
MAZE_COLS = 21
MAZE_ROWS = 17
TILE_SIZE = 32
```

Tiles: `#` Wand, `.` Dot, `O` Power, `-` Gate, `T` Tunnel, `P` Player, `G` Ghost-Haus.  
Maze zentriert: Offset `((1280-672)//2, 80)`. ≥ 80 Dots, 4 Power-Pellets, geschlossener Rand außer einem Tunnel-Paar, Haus 5×3, Player unter dem Haus.

#### 3.A.2 Bewegung

Player 7.0 Tiles/s, Geister 6.2 Tiles/s. 180° sofort, 90° nur im Zentrum (`TURN_EPSILON = 3`). Prefetch `queued`. Tunnel-Wrap; Geister im Tunnel `* 0.6`.

#### 3.A.3 Scoring

Dot 10, Power 50, Geister 200/400/800/1600, Level-Clear 500.  
Power: FRIGHTENED 6.0 s − 0.5 s/Level, min 2.0 s.

#### 3.A.4 Geister

`BLINKY, PINKY, INKY, CLYDE` mit `HOUSE, LEAVE, SCATTER, CHASE, FRIGHTENED, EATEN`.  
Target-Distanz euklidisch, Tie-Break UP/LEFT/DOWN/RIGHT.  
Blinky = Player-Tile (Elroy-light ab < 20 Dots). Pinky = 4 vor Facing. Inky = Punktspiegelung über 2 vor Player. Clyde = Player wenn Distanz > 8, sonst Scatter-Ecke.  
Scatter-Timer Level 1: 7/20/7/20/5/∞. Ab Level 3: 5/20/5/∞.  
Leave-Staffel 0.2 / 0.8 / 2.4 / 4.0 s.  
Zeichnung: Pygame-Primitives, keine SVG-Geister.

#### 3.A.5 Player

3 Leben, INVULN 2.0 s nach Respawn. Kollision Kreis-Radius `TILE_SIZE * 0.35`. Logo-Facing-Cache.

---

### 3.B DONKEY KONG

Messe-Plattformer, **eine** kompakte Baustellen-Szene (kein 4-Board-Original). Gefühl: unten starten, oben Ziel, Fässer weichen, Leitern nutzen, springen.

#### 3.B.1 Bühne

- 6 horizontale Träger (Girders), leicht gegenläufig geneigt (±4° optisch, Kollision als Achsen-Segmente).
- Pro Träger 1–2 Leitern, die den nächsthöheren Träger verbinden. Mindestens ein durchgehender Pfad nach oben.
- Oben links oder mitte: Boss-Platzhalter `KongActor` (rechteckiger Primitive-Körper + getintes Logo 64 px, **nicht** als Player steuerbar).
- Oben rechts: Ziel `GOAL` (Flagge/Portal, bernstein). Berühren = Level-Clear + 500 Punkte + nächste, schnellere Runde.
- Unten: Player-Spawn.

Interne Playfield-Größe: 960×560, zentriert unter HUD.

#### 3.B.2 Physik (arkade, nicht Box2D)

- Laufen: 180 px/s. Gravitation 2200 px/s², Terminal 720 px/s.
- Sprung: Edge-Action, nur wenn `grounded`. `jump_v = -620` px/s.
- Leiter: wenn `dy < 0` und Overlap mit Leiter-Rect ≥ 40 % der Spielerbreite → Climb-State, 140 px/s vertikal, Gravitation aus. `dy > 0` steigt herab. Horizontal auf Leiter gedämpft (0).
- Kein Double-Jump, kein Luft-Steuern über 35 % der Boden-Speed hinaus.
- Träger-Kollision: Füße gegen Oberkante. Durch Leiternlöcher darf der Spieler fallen, wenn nicht im Climb-State.

#### 3.B.3 Fässer und Gefahr

- `KongActor` wirft alle `BARREL_INTERVAL` (1.6 s Level 1, −0.12 s/Level, min 0.7 s) ein Fass.
- Fässer folgen Trägern (rollen in Neigungsrichtung), fallen am Ende eine Ebene tiefer, despawnen unten.
- 15 % Chance: Fass wird zum **Fallfass** (vertikal, schneller) — telegraphiert durch kürzeres Sprite.
- Kollision Spieler/Fass: Kreis-Kreis, außer während Sprung **über** das Fass (Spieler-Fuß y < Fass-Oberkante − 4 px) → +100 Punkte, kein Schaden.
- 3 Leben. Tod: Freeze 1.2 s, Respawn unten. 0 Leben → GAME_OVER.
- Optional ab Level 2: ein Feuergeist auf dem untersten Träger, KI = läuft auf den Spieler zu, kehrt an Leiter/Rand um. Primitive-Zeichnung.

#### 3.B.4 Steuerung und Logo

- LEFT/RIGHT: Facing + Lauf.
- UP/DOWN: Leiter.
- Action: Sprung.
- Logo nicht auf den Kopf drehen. Auf Leitern: letztes L/R-Facing behalten.

#### 3.B.5 Scoring

| Event | Punkte |
|---|---|
| Fass übersprungen | 100 |
| Ebene erreicht (Träger-Index steigt) | 50 (einmal pro Ebene pro Leben) |
| Ziel | 500 |
| Restzeit-Bonus | `int(remaining_seconds) * 10` |

Zeitlimit pro Versuch: 45 s, Anzeige im HUD. Timeout = Tod.

---

### 3.C SNAKE

Klassisches Wachsen auf Raster. Sofort verständlich, härteste Highscore-Kurve.

#### 3.C.1 Feld

```
SNAKE_COLS = 28
SNAKE_ROWS = 16
SNAKE_TILE = 32
```

Feld zentriert unter HUD, 1-Tile-Rand als Wand (sichtbar cyan). Kein Wrap — Wandkontakt ist Tod (Messe: klare Konsequenz).

#### 3.C.2 Bewegung

- Tick-basiert, nicht pixelgenau: `STEP_SECONDS = 0.16` Level 1, `* 0.94` je Food, Minimum 0.07 s.
- Input wird gequeued. **Verbot:** 180° direkt in das erste Körpersegment (Input verwerfen, alte Richtung behalten).
- Pro Step genau ein Tile. Kopf = neu, Schwanz fällt außer nach Food (Wachstum +1).
- Startlänge 4, Start Mitte, Facing RIGHT.

#### 3.C.3 Food und Score

- Ein Food (`O`/Bernstein-Kreis oder getintes Mini-Logo) auf zufälligem freien Tile, nicht auf dem Körper.
- Essen: +10 × aktuelle Länge (steigender Reiz). Level = `1 + foods // 5`.
- Kein zweites Food gleichzeitig.
- 1 Leben: Wand oder Selbstkollision → sofort GAME_OVER (kein Respawn — Snake-Erwartung). Attract darf weich resetten.

#### 3.C.4 Darstellung

- Kopf: `logo_tile[facing]`.
- Körper: Kette `logo_snake_body`, Alpha 220 → 90 zum Schwanz.
- Food pulsiert 2 Hz in der Größe ±8 %.

---

### 3.D BUBBLE SHOT

Aim-and-match, Puzzle-Bobble-Feeling, CHAOS-Farben. Kein originaler Bobble-Sprite.

#### 3.D.1 Spielfeld

- Hex- oder Offset-Row-Grid: `BUBBLE_COLS = 10`, sichtbare Reihen max. 12, Kugel-Durchmesser 36 px.
- Decke fest. Neue Reihe schiebt alle `CEILING_EVERY_SHOTS = 6` Schüsse nach unten (Level 1), ab Level 3 alle 5, ab Level 5 alle 4.
- Bodenlinie 80 px über dem Fußbereich: berührt eine Kugel die Linie → GAME_OVER (nach kurzem Flash).
- Kanone mittig unten. Logo als Kanonenkopf, Lauf = cyan Rechteck.

#### 3.D.2 Zielen und Schuss

- Winkelbereich **−75° … +75°** (0° = senkrecht nach oben).
- LEFT/RIGHT: `±90°/s` analog gehalten. UP/DOWN: Raster ±8°.
- Action-Edge: feuert die **aktuelle** Kugel. Nächste Kugel liegt sichtbar rechts der Kanone (Preview).
- Flug: 720 px/s gerade, Reflektion **nur** an linker/rechter Wand (`vx = -vx`). Keine Decken-Reflektion — Kontakt Decke/Kugel = Snap ins Grid.
- Genau **eine** fliegende Kugel gleichzeitig.

#### 3.D.3 Farben und Match

Farben (max. 4 auf Level 1, 5 ab Level 3):

`#2DE2E6`, `#FF3B3B`, `#FF7AD9`, `#FFB703`, `#3BD1FF`

- Snap: nächster freier Grid-Slot am Kontaktpunkt.
- Nach Snap: Flood-Fill gleiche Farbe. ≥ 3 → entfernen, +50 pro Kugel.
- Hängende Gruppen ohne Verbindung zur Decke fallen, +20 pro Fall-Kugel.
- Kette in einem Schuss: Multiplier 1, 2, 3 … auf den Fall-Bonus.
- Level-Clear: Feld leer → +1000, neue kompaktere Startformation, schnelleres Ceiling.

#### 3.D.4 Startformation und Leben

- 5 gefüllte Reihen, zufällig aber **keine** sofortigen 3er auf Start (Generator retry max. 20).
- 3 Leben nur bei „Bodenlinie berührt“? Nein: **1 Versuch** pro Runde (Puzzle-Klarheit). GAME_OVER bei Bodenkontakt. Clear ist der einzige Fortschritt.
- Score überlebt Level-Clear in derselben PLAYING-Session (mehrere Felder, ein Leben).

#### 3.D.5 Darstellung

- Ruhende Kugeln: gefüllte Kreise + 2 px Outline + kleines Logo-Watermark (alpha 40), damit CHAOS sichtbar bleibt ohne Lesbarkeit zu töten.
- Fliegende Kugel: `logo_bubble` getintet.
- Aim-Hilfslinie: gepunktet, max. 1 Reflektion, Alpha 90 — Pflicht für Messe (ohne sie ist das Spiel unspielbar am Pult).

---

### 3.E FROGGER

Raster-Queren: Straße, Mittelstreifen, Fluss, 5 Nester.

#### 3.E.1 Layout (13 Reihen × 15 Spalten)

Von unten nach oben:

0. Safe Home (Startreihe, Player-Spawn Mitte)  
1–4. Straße: 4 Lanes, Fahrzeuge  
5. Safe Median  
6–9. Wasser: 4 Lanes, Holz/Schildkröten  
10. Bank  
11. 5 Nester (`HOME`), getrennt durch Mauern  
12. (oben, dekorativ)

`FROG_TILE = 40` → 15×40 = 600 px breit, 13×40 = 520 px hoch, zentriert.

#### 3.E.2 Bewegung

- Input ist **Edge pro Richtung**: ein Tap = ein Tile. Halten feuert **nicht** automatisch (kein Rutschen).
- Cooldown `HOP_COOLDOWN = 0.12` s, damit Stick-Prellen keine Doppeltreppe auslöst.
- Illegal: in Wand/Nest-Mauer, aus dem Feld, in ein bereits gefülltes Nest.
- Wasser **ohne** Floater unter den Füßen (nach dem Hop, 1 Frame Toleranz) = Tod.
- Straße: AABB gegen Fahrzeuge = Tod.

#### 3.E.3 Hazard-Bewegung

- Jede Lane hat eigene Speed und Richtung, gegenläufig benachbart.
- Autos: 2–3 Rects, Lücken immer ≥ 2 Tiles bei Level 1.
- Fluss: Logs 2–4 Tiles lang; Schildkröten können ab Level 2 alle 3 s für 1.0 s tauchen.
- Spieler auf Floater erbt `vx` der Lane (pixelgenau zwischen Hops, gerastert beim nächsten Hop).
- Wrap: Hazards verlassen links und kommen rechts wieder (und umgekehrt).
- Level+1 wenn alle 5 Nester gefüllt: Speeds `* 1.12`, eine zusätzliche Auto-Lane-Dichte, Timer härter.

#### 3.E.4 Leben, Zeit, Score

- 3 Leben. Tod: Respawn Startreihe, aktueller Nest-Fortschritt bleibt.
- Timer pro Versuch: 20 s → 0 = Tod. Reset bei erfolgreichem Nest.
- Nest erreichen: +200 + `int(remaining_s)*10`. Vorwärts-Hop +10. Alle 5 Nester: +500 und Level-Up, Nester leeren.

#### 3.E.5 Darstellung

- Player: `logo_tile[facing]`.
- Autos: Neon-Rechtecke (rot/pink), keine Sprite-Roms.
- Logs: dunkles Cyan-Braun-Rechteck.
- Nester: bernstein-Mulde; gefüllt = Mini-Logo 20 px.

---

## 4. Implementierungsauftrag

Reihenfolge **zwingend** (jedes Game nach Shell spielbar committen, nicht fünf halbfertige):

1. Shared Shell: Display, Input, LogoAsset, Highscore, GAME_SELECT, ATTRACT-Gerüst, GAME_OVER.
2. `PacmanMode` vollständig (Abnahme §5.A).
3. `SnakeMode` (schnellster zweiter Titel).
4. `FroggerMode`.
5. `BubbleShotMode`.
6. `DonkeyKongMode`.
7. Attract rotiert durch alle implementierten Games; fehlende Modes dürfen noch nicht im Carousel stehen **oder** sitzen als `Coming Soon` — **verboten**. Carousel zeigt nur fertige Games. Zielstand: alle fünf fertig.

Weitere Regeln:

1. `requirements.txt` + `setup_pi5.sh` für Pi 5 / Bookworm.
2. README: `python3 main.py`, `CHAOS_WINDOWED=1`, kurze Spielübersicht der fünf Titel.
3. Ohne `logo.svg` starten alle fünf mit Fallback.
4. Mit `logo.svg` ist das Logo in jedem Titel der Avatar (siehe 1.4).
5. Tastatur allein reicht für alle Spiele inkl. Action (Space).
6. Kein Netzwerk, kein Runtime-pip, keine Telemetrie.
7. Bezeichner Englisch wie in diesem Dokument; keine `TODO`/`pass` in Gameplay-Pfaden.
8. Pi-Start:

```
chmod +x setup_pi5.sh
./setup_pi5.sh
python3 main.py
```

---

## 5. Abnahmekriterien (Definition of Done)

### 5.0 Shared Shell

- [ ] Start auf Pi 5 und Desktop (windowed) ohne Crash, ohne SVG, ohne Gamepad.
- [ ] Carousel zeigt genau fünf Titel, Wrap, Hi-Score wechselt pro Slot.
- [ ] Start lädt das gewählte Spiel; Game-Over kehrt zur Auswahl auf demselben Slot zurück.
- [ ] 12 s Idle → Attract; Attract rotiert Titel; Input → SELECT.
- [ ] 30 s Idle in PLAYING → SELECT, kein Highscore-Write.
- [ ] Highscores getrennt pro Game, überleben Neustart; Legacy-`entries` → PACMAN.
- [ ] Logo-Pipeline cairosvg → pygame → Fallback, Logs auf stdout.
- [ ] 8BitDo D-Pad, Analog, A/Start und Keyboard parallel; Action ist Edge.
- [ ] Fullscreen-Kiosk, Cursor aus, Shift+Q beendet.
- [ ] ≥ 50 FPS in jedem aktiven Spiel.

### 5.A Pac-Man

- [ ] Richtungs-Logo, 4 Geister-Persönlichkeiten, Frightened/Eaten, Dots, Power, Tunnel, 3 Leben, Level-Clear.

### 5.B Donkey Kong

- [ ] Laufen, Leitern, Sprung, Fässer mit Träger-Logik, Ziel oben, Zeitlimit, Fass-Skip-Punkte, 3 Leben.

### 5.C Snake

- [ ] Queue ohne 180°-Selbstkill, Wachstum, Speed-up, Wand = Tod, Kopf = Logo.

### 5.D Bubble Shot

- [ ] Winkeln, Schuss, Wandreflex, Grid-Snap, Match-≥3, Fallgruppen, Aim-Linie, Ceiling-Push, Boden = Out.

### 5.E Frogger

- [ ] Edge-Hops, Autos, Logs, Wasser-Tod, 5 Nester, Timer, Level nach Full-Home.

---

## 6. Self-Check vor dem Commit der Implementierung

1. Existieren `GameMode` und fünf Mode-Klassen, auch wenn noch in `main.py` gebündelt?
2. Eine Shared-Quelle für Display/Input/Logo/Highscore?
3. Wird `logo.svg` niemals pro Frame gerastert — auch nicht für Bubble-Winkel (Cache!)?
4. Sind Diagonalen in Pac-Man/Snake/Frogger unmöglich? (DK: in der Luft begrenztes Strafen erlaubt, kein 8-Wege-Run.)
5. Kann das Kabinett 2 Minuten ohne Input im Select/Attract-Zyklus allein laufen?
6. Ist `data/highscores.json` gitignored?
7. Zeigt SELECT wirklich alle fünf **spielbaren** Titel — keinen Platzhalter-Slot?
8. Crash in einem Mode fängt die Shell und kehrt zu SELECT zurück?

Ende des Master-Prompts. Dieses Dokument ist die einzige Wahrheitsquelle für die Code-Generierung.
