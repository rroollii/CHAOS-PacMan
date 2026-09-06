# CHAOS Arcade — Master-Prompt / System-Instruction Set

**Dokumenttyp:** Pflichtenheft + Self-Instruction Set für Code-Generierung  
**Produktname (UI):** `CHAOS ARCADE`  
**Repo-/Ordnername:** `CHAOS_PacMan` (unverändert; kein Rename-Zwang)  
**Zielplattform:** Raspberry Pi 5 (64-bit Raspberry Pi OS)  
**Stack:** Python 3.11+ / Pygame 2  
**Eingabe:** 8BitDo DIY Kit (Bluetooth Arcade-Stick) + Tastatur-Pfeiltasten  
**Spieler-Asset:** `assets/logo.svg` (Firmenlogo, Vektor) — **in jedem Spiel** die Spielfigur  
**Betriebsart:** Unbeaufsichtigtes Messe-Kiosk am digitalen Pult  
**Öffentliche Bedienung:** nur das **freigeschaltete** Spiel starten/spielen — kein öffentlicher Spielwechsel  
**Operator-Spielwechsel:** nur über versteckte Tastenkombination (siehe 2.3.5)  
**Highscore:** Namenspflicht, Top-10 **je Spiel**, sichtbar in jedem Nicht-Spiel-State  

**Spielkatalog (verbindlich, genau diese fünf, in dieser Reihenfolge):**

| `GameId` | UI-Titel | Genre-Vorbild | Kernschleife (Messe, 30–90 s) |
|---|---|---|---|
| `PACMAN` | PAC-MAN | Pac-Man | Labyrinth, Dots, 4 Geister |
| `DONKEY_KONG` | DONKEY KONG | Donkey Kong | Plattformen, Leitern, Fässer, Sprung |
| `SNAKE` | SNAKE | Snake | Wachsen, nicht selbst treffen |
| `BUBBLE_SHOT` | BUBBLE SHOT | Puzzle Bobble / Bubble Shooter | Zielen, schießen, 3er-Match |
| `FROGGER` | FROGGER | Frogger | Straßen/Fluss queren, 5 Ziele |

Dieses Dokument ist verbindlich. CHAOS Arcade ist **kein** reiner Pac-Man-Klon. Pac-Man ist das **erste** Spiel im Kabinett und der **Default** nach Erststart, nicht das einzige. Besucher spielen immer nur das vom Operator freigeschaltete Spiel. Jede nachfolgende Implementierung muss sich **wortgetreu** an diese Vorgaben halten. Abweichungen sind nur zulässig, wenn sie einen Laufzeitfehler auf dem Raspberry Pi 5 verhindern — und müssen dann im Code kommentiert werden.

Rechtlicher Rahmen: Es werden **keine** originalen ROM-Assets, Sprites, Melodien oder Markenzeichen Dritter eingebettet. Mechanik und Feeling dürfen anklingen; visuelle Identität ist ausschließlich CHAOS (Logo + Neon-Palette).

---

## 0. Nicht verhandelbare Leitplanken

### 0.1 Betriebsziel

CHAOS Arcade ist ein **Multi-Game-Mitmach-Kabinett mit gesperrtem Titel**. Ein Messebesucher greift zum 8BitDo-Arcade-Stick, sieht das **aktuell freigeschaltete** Spiel plus dessen Top-10, startet in ≤ 3 Sekunden eine kurze Runde, gibt bei Top-10-Qualifikation **zwingend** seinen Namen ein, und das Gerät kehrt selbstständig zum Idle-Screen desselben Spiels zurück.

- Es gibt **kein** öffentliches Spielemenü, **kein** Carousel, **kein** Dateimenü, **kein** OS-UI, **kein** Beenden über sichtbare Buttons.
- Links/Rechts **wechselt das Spiel nicht**. Spielwechsel nur über die Operator-Kombination (2.3.5). Kein On-Screen-Hinweis darauf.
- Vollbild-Verlassen nur über verstecktes Operator-Hotkey (siehe 2.3.4 / 2.5).
- Jedes der fünf Spiele muss **allein mit Stick + einem Action-Button** bedienbar sein. Namenseingabe ebenfalls nur mit Stick + Action/Start.
- Typische Runde: **30–90 Sekunden**. Kein Spiel darf eine Einarbeitungszeit > 3 Sekunden brauchen.
- Das Firmenlogo ist in **allen** Spielen der Avatar (Mund/Kopf, Kletterer, Schlangenkopf, Kanone/Kugel, Springer).
- Solange **nicht** gespielt wird (`GAME_SELECT`, `ATTRACT_MODE`, `GAME_OVER`, `NAME_ENTRY`), ist die **Top-10 des aktuellen Spiels** sichtbar — mit Rang, Name, Score.

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
- Pro Frame maximal die aktive Spielszene plus HUD. Inaktive Games werden nicht simuliert (außer Attract-Demo des featured Game).
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
├── states.py               # Shell-States: SELECT, ATTRACT, PLAYING, GAME_OVER, NAME_ENTRY
├── highscore.py            # JSON Persistenz + Name, getrennt pro GameId
├── cabinet.py              # featured GameId Persistenz (Operator-Wahl)
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
├── attract.py              # Demo nur des featured Game; keine Titelrotation
├── assets/
│   └── logo.svg            # Firmenlogo (kann fehlen)
├── data/
│   ├── highscores.json     # wird zur Laufzeit erzeugt
│   └── cabinet.json        # featured GameId; wird zur Laufzeit erzeugt
├── requirements.txt
├── setup_pi5.sh
├── .gitignore              # data/*.json, __pycache__, .venv
├── MASTER_PROMPT.md
└── README.md
```

Die erste Auslieferung darf alles in `main.py` vereinen, **muss** aber `GameId`, `GameMode`, `CabinetStore`, `HighscoreStore`, `StateId.NAME_ENTRY` und die fünf Mode-Klassen (`PacmanMode`, `DonkeyKongMode`, `SnakeMode`, `BubbleShotMode`, `FroggerMode`) namentlich enthalten.

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
featured = CabinetStore.load()          # persistiert; Default PACMAN
state = GAME_SELECT                     # Idle des featured Game — kein öffentliches Menü
last_input_ts = now
while running:
    dt = clock.tick(60) / 1000.0
    events = pygame.event.get()
    command = InputMap.poll(events)
    if command.activity:
        last_input_ts = now
    state.on_command(command)
    state.update(dt)
    if state != NAME_ENTRY and now - last_input_ts >= INACTIVITY_SECONDS:
        force_transition(GAME_SELECT)   # NAME_ENTRY hat eigenen 20-s-Timer
    state.draw(screen)
    pygame.display.flip()
```

Nur das **aktive** `GameMode` erhält `update`/`draw`. `dt` in Sekunden, zeitbasiert.

### 2.2 State-Machine (Shell)

```
class StateId(Enum):
    GAME_SELECT = "GAME_SELECT"   # Idle / Titel des featured Game + Top-10
    ATTRACT_MODE = "ATTRACT_MODE"
    PLAYING = "PLAYING"
    GAME_OVER = "GAME_OVER"
    NAME_ENTRY = "NAME_ENTRY"
```

`START_SCREEN` entfällt. Ein öffentliches Spiele-Carousel **existiert nicht**.  
`GAME_SELECT` ist der Idle-Screen des **einen** freigeschalteten Titels.

`GameState`: `enter()`, `exit()`, `on_command(cmd)`, `update(dt)`, `draw(surf)`.  
`Game.change_state(new_id)` ruft `exit()` dann `enter()`.

`featured: GameId` ist Shell-Zustand, nicht Spielerwahl. Persistenz über `CabinetStore` (`data/cabinet.json`). Erststart: `PACMAN`. Operator-Wechsel schreibt sofort.

#### 2.2.1 GAME_SELECT (Idle)

Kein Carousel. Keine Nachbar-Spiele. Kein `◀ WÄHLEN ▶`.

Layout (1280×720):

- Oben: Logo 160 px + `CHAOS ARCADE` + UI-Titel des **featured** Game (z. B. `PAC-MAN`).
- Eine Zeile Mechanik des featured Game (deutsch, max. 28 Zeichen).
- Mitte/rechts: **Top-10-Tafel** dieses Spiels (Pflicht, siehe 2.3.6). Leere Plätze als `---  --------    000000`.
- Unten blinkend: `START SPIELEN` — kein Hinweis auf andere Titel, keine Pfeile.

Eingabe:

- `command.start` oder `command.any_action` → `PLAYING` mit `registry[featured].reset()`.
- `command.dx` / `command.dy` **ohne** Operator-Modifier: ignorieren (kein Titelwechsel, kein Listen-Scroll nötig — 10 Zeilen passen).
- Operator-Kombo (2.3.5) wechselt `featured`, lädt die neue Top-10, bleibt in `GAME_SELECT`.
- Nach `ATTRACT_IDLE_SECONDS = 12` ohne Input → `ATTRACT_MODE` desselben featured Game.

#### 2.2.2 ATTRACT_MODE

- Spielt eine **deterministische Demo nur des featured Game**. **Keine** Rotation zu anderen `GameId`. `ATTRACT_ROTATE_SECONDS` entfällt.
- HUD: `DEMO` + Spielname.
- **Top-10-Tafel** des featured Game bleibt sichtbar (rechte oder untere Leiste, Demo darf nicht die Namen verdecken).
- Jeder **öffentliche** Input → sofort `GAME_SELECT` (nicht direkt ins Spiel).
- Operator-Kombo in Attract: setzt `featured` neu, bricht Attract ab → `GAME_SELECT` des neuen Titels.
- Attract schreibt **keine** Highscores und verbraucht keine Leben persistent.
- Gesamtdauer einer Attract-Session max. 40 s, danach zurück `GAME_SELECT` (Idle-Loop: Select 12 s → Attract → Select, immer dasselbe featured Game).

#### 2.2.3 PLAYING

- Instanziiert genau `registry[featured]`.
- HUD oben 80 px: Spielname, Score, Leben/Versuche, Level.
- Die Top-10-Tafel **ruht** während `PLAYING` (nur laufender Score im HUD).
- Pause existiert **nicht**.
- `GameMode` signalisiert Ende über `Result.GAME_OVER` oder `Result.QUIT_TO_SELECT` (letzteres nur durch Inaktivität der Shell).
- Leben, Tempo, Level-Steigerung: **pro Spiel** in §3.x, nicht global identisch.
- Operator-Spielwechsel ist in `PLAYING` **gesperrt** (kein Mid-Game-Switch).

#### 2.2.4 GAME_OVER

- Overlay: Spielname, `GAME OVER`, Score.
- Top-10-Tafel des gespielten Game bleibt sichtbar.
- Qualifikation (`score > 0` und (Liste < 10 oder `score >=` 10. Platz)): **kein** Schreiben in `enter()`. Wechsel nach 1.2 s oder sofort bei Start/Action → `NAME_ENTRY`. Ohne Qualifikation kein Name, kein Write.
- Nicht qualifiziert: 6 s oder Start/Action → `GAME_SELECT` (featured unverändert). Operator-Kombo in diesem Fall erlaubt (featured wechselt, die Runde wurde nicht gespeichert).
- Qualifiziert: Operator-Kombo **gesperrt**, bis `NAME_ENTRY` abgeschlossen oder per Timeout verworfen ist.

#### 2.2.5 NAME_ENTRY

Pflicht, sobald die Runde die Top-10 qualifiziert. **Kein Überspringen**, kein leerer Name, kein automatisches `AAA`.

- Alphabet-Tafel: `A–Z`, `0–9`, `−` (Bindestrich), `←` (löschen), `END`.
- Stick: Cursor in der Tafel (kein Diagonal-Pick; `dx`/`dy` disjunkt).
- `command.action` (Edge): Buchstabe anhängen (max. `NAME_MAX_LEN = 8`); `←` löscht ein Zeichen; `END` reicht `command.start` gleich.
- `command.start`: absenden, **nur wenn** `len(name) >= NAME_MIN_LEN = 3`. Sonst ignorieren, Hinweis `3 ZEICHEN MIN.` 1 s.
- Name wird intern uppercased, nur der erlaubte Zeichensatz. Leading/Trailing-Spaces stripped; interne Spaces verboten (Alphabet enthält kein Space).
- Nach gültigem Absenden: genau einmal `HighscoreStore.add(featured, name, score, level)` → `GAME_SELECT`. Die Top-10 ist dort sofort aktualisiert.
- Inaktivität in `NAME_ENTRY`: `NAME_ENTRY_SECONDS = 20`. Timeout **verwirft** den Score (kein anonymer Write) und geht zu `GAME_SELECT`. Jeder Input resetet den Timer.
- Operator-Spielwechsel in `NAME_ENTRY` **gesperrt** (Score gehört zum gerade gespielten Titel).

Default-Anzeige: leerer Name, Cursor auf `A`. Die Top-10 zeigt den neuen Rang als blinkende Leerzeile (`--  ........  score`) bis zum Absenden.

### 2.3 Messe-Kiosk-Features

#### 2.3.1 Inaktivitäts-Timer

```
INACTIVITY_SECONDS = 30
ATTRACT_IDLE_SECONDS = 12
NAME_ENTRY_SECONDS = 20
```

`ATTRACT_ROTATE_SECONDS` ist **entfernt** (Attract bleibt auf dem featured Game).

- Aktivität = Richtung, Action, Start. Analog unter `AXIS_DEADZONE = 0.45` zählt nicht. Operator-Kombo zählt als Aktivität.
- Timeout in `PLAYING`/`GAME_OVER` → `GAME_SELECT`. Score aus `PLAYING` wird **nicht** gespeichert. Score aus `GAME_OVER` ist zu diesem Zeitpunkt noch nicht geschrieben (Write erst nach `NAME_ENTRY`).
- Der 30-s-Global-Timer gilt **nicht** in `NAME_ENTRY`.
- Timeout in `NAME_ENTRY` (20 s): Score verwerfen, `GAME_SELECT`.

#### 2.3.2 Highscore-Speicher

Datei: `data/highscores.json`

```json
{
  "updated_at": "ISO-8601",
  "games": {
    "PACMAN": [{"name": "ROL", "score": 12340, "level": 2, "ts": "ISO-8601"}],
    "DONKEY_KONG": [],
    "SNAKE": [],
    "BUBBLE_SHOT": [],
    "FROGGER": []
  }
}
```

`HighscoreStore.add(game_id, name, score, level) -> int` gibt den 1-basierten Rang zurück (0 = nicht aufgenommen).

- Pro `GameId` maximal 10 Einträge, sortiert `score` desc, dann `ts` desc.
- `name` ist Pflicht: 3–8 Zeichen aus `[A-Z0-9-]`. Fehlt oder ungültig → **kein Write**.
- Atomar: `highscores.json.tmp` + `os.replace`.
- Corrupt → leere Listen für alle fünf Keys, Rebuild beim Write.
- Altes Schema ohne `games`-Map (nur `entries`) einmalig nach `PACMAN` migrieren.
- Legacy-Einträge ohne `name` → `name = "---"` (einmalig, bleiben stehen, zählen in die Top-10).
- Score `0` wird nie geschrieben.
- `data/` wird beim ersten Write erzeugt.

#### 2.3.2b Cabinet-Speicher (featured Game)

Datei: `data/cabinet.json`

```json
{ "featured_game": "PACMAN", "updated_at": "ISO-8601" }
```

- `CabinetStore.load() -> GameId`, `CabinetStore.save(game_id)`.
- Ungültiger/fehlender Key → `PACMAN`.
- Atomar analog Highscore.
- `Shift+R` löscht Highscores, **nicht** das featured Game.

#### 2.3.3 Kiosk-Display

- Pi: `set_mode((0, 0), FULLSCREEN)`.
- Dev: `CHAOS_WINDOWED=1` → 1280×720-Fenster.
- Interne Surface immer 1280×720, danach `smoothscale` aufs Fenster.
- `pygame.mouse.set_visible(False)`.

#### 2.3.4 Operator-Hotkeys

Kein HUD-Hinweis auf irgendeine dieser Kombinationen.

- `Q` + `Left-Shift`: Beenden.
- `F11`: Fullscreen toggle (Dev).
- `R` + `Left-Shift`: Highscores **aller** Spiele löschen (featured Game bleibt).
- `1`…`5`: stille Direktwahl des featured Game (Dev/Operator), erlaubt in `GAME_SELECT`, `ATTRACT_MODE` und in `GAME_OVER` **ohne** Qualifikation — nicht in `PLAYING` / `NAME_ENTRY` / qualifiziertem `GAME_OVER`.

#### 2.3.5 Operator-Spielwechsel (verbindlich)

Öffentliches Links/Rechts **darf das Spiel nicht wechseln**. Nur wer die Kombination kennt, schaltet den Kabinett-Titel um.

**Modifier (gehalten):**

| Quelle | Modifier |
|---|---|
| Tastatur | `K_LSHIFT` |
| 8BitDo / Gamepad | Button **6 oder 8** (Select) **oder** Button **7 oder 9** (Start), gehalten. **Nicht** Button 0/1 (Action). |

**Schaltgeste:** Modifier gehalten + `Left`/`Right` Edge → `featured` ± 1, Wrap Pac-Man ↔ Frogger. Sofort `CabinetStore.save`. Titel + Top-10 wechseln in derselben Frame-Logik.

Zusätzlich Dev: Tasten `1`…`5` (siehe 2.3.4).

Regeln:

- Wirkt in `GAME_SELECT`, `ATTRACT_MODE` und in `GAME_OVER` **ohne** anstehende Namenseingabe.
- Wirkt **nicht** in `PLAYING`, **nicht** in `NAME_ENTRY` und **nicht** in qualifiziertem `GAME_OVER`.
- Action (Button 0/1 / Space) ist **kein** Modifier — sonst startet jeder Messebesucher unbeabsichtigt den Wechsel.
- Kurzes Start-Tap ohne Richtung bleibt `start` (Spiel beginnen / Overlay schließen).
- Start/Select **gehalten** ohne Richtung: kein Spielstart, kein Switch (entprellt die Kombo).
- Nach Switch: 200 ms Cyan-Rahmenblitz, **kein** Text `OPERATOR` / `GEHEIM`. Log auf stdout: `[operator] featured=SNAKE`.
- Attract wird beim Switch abgebrochen.

#### 2.3.6 Top-10-Tafel (sichtbar, wenn nicht gespielt wird)

Komponente `draw_highscore_table(surf, game_id, highlight_rank=None)`.

Pflicht in `GAME_SELECT`, `ATTRACT_MODE`, `GAME_OVER`, `NAME_ENTRY`. In `PLAYING` nicht zeichnen.

```
HI-SCORE  PAC-MAN
01  ROL      012340
02  MIA      009100
...
10  ---      000000
```

- Monospace, Rang 2-stellig, Name 8 Zeichen links, Score 6-stellig zero-padded.
- Lesbar ab 1,5 m: Zeilenhöhe ≥ 28 px, Farbe Warmweiß, Rang-1 Bernstein.
- `highlight_rank` (nach neuer Qualifikation / während NAME_ENTRY): diese Zeile blinkt cyan.
- Immer genau 10 Zeilen, auch wenn weniger Einträge existieren.

### 2.4 Gamepad / Keyboard Event-Loop

```
@dataclass(frozen=True)
class Command:
    dx: int              # -1, 0, +1
    dy: int              # -1, 0, +1
    start: bool
    action: bool         # Edge: A / Space — Sprung, Schuss, Bestätigen
    action_held: bool    # Level: gehalten (für optionales Charging; Default ungenutzt)
    operator_held: bool  # Shift / Select / Start (nicht Action) gehalten
    operator_switch: int # -1, 0, +1 — nur wenn operator_held und Left/Right-Edge
    any_action: bool
    activity: bool
    quit_combo: bool
```

`dx/dy` disjunkt, keine Diagonalen. Priorität: D-Pad → Analog (größere Achse) → Tastatur → (0,0).

Wenn `operator_switch != 0`, setzt die Shell `dx = 0` für die öffentliche Semantik (kein gleichzeitiges Navigieren in NAME_ENTRY). `start` ist in diesem Frame `False` (gehaltenes Start löst kein Spielstart aus).

| Aktion | Keyboard | Gamepad |
|---|---|---|
| Hoch | `K_UP`, `K_w` | HAT y=+1 oder Axis 1 < −DEADZONE |
| Runter | `K_DOWN`, `K_s` | HAT y=−1 oder Axis 1 > +DEADZONE |
| Links | `K_LEFT`, `K_a` | HAT x=−1 oder Axis 0 < −DEADZONE |
| Rechts | `K_RIGHT`, `K_d` | HAT x=+1 oder Axis 0 > +DEADZONE |
| Action / Sprung / Schuss | `K_SPACE`, `K_LCTRL` | Button 0 (A), Button 1 (B) |
| Start / Bestätigen | `K_RETURN` | Button 7 / 9 (Start) **oder** Action, wenn der State Action als Start akzeptiert |
| Operator-Modifier | `K_LSHIFT` | Button 6 / 8 (Select), 7 / 9 (Start) gehalten |
| Operator-Switch | Shift + Links/Rechts | Select/Start gehalten + Links/Rechts |
| Aktivität | jede der oben | jede der oben |

- Joystick-Hot-Plug ohne Crash.
- `HAT_Y_INVERT = True` als Pi-Default.
- `START_BUTTONS = {0, 1, 7, 9}` für **kurzes** Start in SELECT/GAME_OVER/NAME_ENTRY. Gehaltenes 7/9 mit Richtung ist Operator, nicht Start.
- `OPERATOR_BUTTONS = {6, 7, 8, 9}`. Schnittmenge mit Start ist Absicht: derselbe Start-Button am 8BitDo DIY Kit dient als Modifier, sobald er gehalten wird.
- `action` ist **Edge** (down in diesem Frame), sonst feuert Bubble Shot Dauerfeuer.

#### 2.4.1 Command-Semantik in der Shell

| State | Richtung (ohne Operator) | Action / Start | Operator-Switch |
|---|---|---|---|
| GAME_SELECT | ignoriert | → PLAYING | featured ± 1, bleibt SELECT |
| ATTRACT_MODE | → GAME_SELECT | → GAME_SELECT | featured ± 1, → SELECT |
| PLAYING | an `GameMode` | an `GameMode` (`start` ignorieren) | ignoriert |
| GAME_OVER | activity hält Timer | → NAME_ENTRY (qualifiziert) oder SELECT | featured ± 1 nur wenn **nicht** qualifiziert |
| NAME_ENTRY | Cursor auf Alphabet | Buchstabe / END bzw. Absenden | ignoriert |

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

1. Shared Shell: Display, Input, LogoAsset, Highscore inkl. Name, CabinetStore, GAME_SELECT-Idle + Top-10-Tafel, Operator-Switch, ATTRACT-Gerüst (nur featured), GAME_OVER, NAME_ENTRY.
2. `PacmanMode` vollständig (Abnahme §5.A). Featured-Default = PACMAN.
3. `SnakeMode` (schnellster zweiter Titel). Operator kann darauf schalten, sobald spielbar.
4. `FroggerMode`.
5. `BubbleShotMode`.
6. `DonkeyKongMode`.
7. Attract spielt **nur** das featured Game. Ein unfertiger Titel darf **nicht** per Operator erreichbar sein. Zielstand: alle fünf fertig und per Kombo wählbar. Kein `Coming Soon`, kein öffentliches Carousel.

Weitere Regeln:

1. `requirements.txt` + `setup_pi5.sh` für Pi 5 / Bookworm.
2. README: `python3 main.py`, `CHAOS_WINDOWED=1`, kurze Spielübersicht, **ohne** die Operator-Kombo preiszugeben (die steht nur hier im Prompt).
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
- [ ] Idle zeigt **ein** featured Game (Default PACMAN) plus dessen vollständige Top-10. Kein Carousel, keine Nachbar-Titel, keine Wähl-Pfeile.
- [ ] Öffentliches Links/Rechts wechselt das Spiel **nicht**. Shift+Links/Rechts bzw. Start/Select gehalten + Links/Rechts wechselt featured (Wrap), persistiert in `cabinet.json`, loggt `[operator]`.
- [ ] Tasten `1`…`5` schalten featured still; unfertige Titel sind nicht erreichbar.
- [ ] Start/Action lädt das featured Spiel; Game-Over kehrt zum Idle **desselben** Titels zurück (außer Operator hat danach umgeschaltet).
- [ ] Qualifizierter Score öffnet NAME_ENTRY; Absenden erst ab 3 Zeichen; Write nur mit Name. Timeout 20 s verwirft den Score.
- [ ] Unqualifizierter Score (0 oder unter Platz 10 bei voller Liste): kein NAME_ENTRY, kein Write.
- [ ] Top-10-Tafel mit Name+Score ist in SELECT, ATTRACT, GAME_OVER, NAME_ENTRY sichtbar; in PLAYING nicht.
- [ ] 12 s Idle → Attract **desselben** Titels (keine Titelrotation); Input → SELECT.
- [ ] 30 s Idle in PLAYING → SELECT, kein Highscore-Write.
- [ ] Highscores getrennt pro Game, inkl. Name, überleben Neustart; Legacy-`entries` → PACMAN mit `name = "---"`.
- [ ] Logo-Pipeline cairosvg → pygame → Fallback, Logs auf stdout.
- [ ] 8BitDo D-Pad, Analog, A/Start/Select und Keyboard parallel; Action ist Edge; Start gehalten + Richtung = Operator, nicht Spielstart.
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
2. Eine Shared-Quelle für Display/Input/Logo/Highscore/Cabinet?
3. Wird `logo.svg` niemals pro Frame gerastert — auch nicht für Bubble-Winkel (Cache!)?
4. Sind Diagonalen in Pac-Man/Snake/Frogger unmöglich? (DK: in der Luft begrenztes Strafen erlaubt, kein 8-Wege-Run.)
5. Kann das Kabinett 2 Minuten ohne Input im Select/Attract-Zyklus **desselben** featured Game allein laufen?
6. Sind `data/highscores.json` und `data/cabinet.json` gitignored?
7. Gibt es **kein** öffentliches Carousel und keinen `Coming Soon`-Slot? Ist Spielwechsel ausschließlich die Operator-Kombo?
8. Crash in einem Mode fängt die Shell und kehrt zu SELECT zurück?
9. Wird kein Highscore ohne gültigen Namen (3–8, `[A-Z0-9-]`) geschrieben?
10. Ist die Operator-Kombo nirgends im HUD oder in der README erklärt?

Ende des Master-Prompts. Dieses Dokument ist die einzige Wahrheitsquelle für die Code-Generierung.
