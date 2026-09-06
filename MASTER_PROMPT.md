# CHAOS Arcade — Master-Prompt / System-Instruction Set

**Dokumenttyp:** Pflichtenheft + Self-Instruction Set für Code-Generierung  
**Produktname (UI):** `CHAOS ARCADE`  
**Repo-/Ordnername:** `CHAOS_PacMan` (unverändert; kein Rename-Zwang)  
**Zielplattform:** Raspberry Pi 5 (64-bit Raspberry Pi OS)  
**Stack:** Python 3.11+ / Pygame 2  
**Eingabe:** 8BitDo DIY Kit (Bluetooth Arcade-Stick) + Tastatur-Pfeiltasten  
**Spieler-Assets:** `assets/logo_face.svg`, `assets/logo_mark.svg`, `assets/logo_badge.svg` — das CHAOS-Logo ist **in jedem Spiel der einzige Held**  
**Betriebsart:** Unbeaufsichtigtes Messe-Kiosk am digitalen Pult  
**Öffentliche Bedienung:** nur das **freigeschaltete** Spiel starten/spielen — kein öffentlicher Spielwechsel  
**Operator-Spielwechsel:** nur über versteckte Tastenkombination (siehe 2.3.5)  
**Highscore:** Namenspflicht, Top-10 **je Spiel**, sichtbar in jedem Nicht-Spiel-State  

**Spielkatalog (verbindlich, genau diese sieben, in dieser Reihenfolge — Maximum, keine weiteren Titel):**

| `GameId` | UI-Titel | Genre-Vorbild | Kernschleife (Messe, 30–90 s) |
|---|---|---|---|
| `PACMAN` | PAC-MAN | Pac-Man | Labyrinth, Dots, 4 Geister |
| `DONKEY_KONG` | DONKEY KONG | Donkey Kong | Plattformen, Leitern, Fässer, Sprung |
| `SNAKE` | SNAKE | Snake | Wachsen, nicht selbst treffen |
| `BUBBLE_SHOT` | BUBBLE SHOT | Puzzle Bobble / Bubble Shooter | Zielen, schießen, 3er-Match |
| `FROGGER` | FROGGER | Frogger | Straßen/Fluss queren, 5 Ziele |
| `INVADERS` | INVADERS | Space Invaders | Formation, schießen, Wellen |
| `BREAKOUT` | BREAKOUT | Breakout | Schläger, Ball, Steine |

Bewusst **nicht** im Katalog (auch nicht als späterer Nachzug): Tetris-Klone (Marke + zu lange Partien), Endless Runner (überlappt Frogger), Top-Down-Racer (Session zu lang), Q*bert (Diagonale), Pinball (zwei Flipper). Das Kabinett ist mit sieben Titeln voll.

Dieses Dokument ist verbindlich. CHAOS Arcade ist **kein** reiner Pac-Man-Klon. Pac-Man ist das **erste** Spiel im Kabinett und der **Default** nach Erststart, nicht das einzige. Es gibt genau **sieben** Titel. Besucher spielen immer nur das vom Operator freigeschaltete Spiel. Jede nachfolgende Implementierung muss sich **wortgetreu** an diese Vorgaben halten. Abweichungen sind nur zulässig, wenn sie einen Laufzeitfehler auf dem Raspberry Pi 5 verhindern — und müssen dann im Code kommentiert werden.

Rechtlicher Rahmen: Es werden **keine** originalen ROM-Assets, Sprites oder Melodien Dritter eingebettet und **keine** offiziellen Logo-Dateien (SVG/PNG) von Microsoft oder Nintendo geladen. Keine Produktnamen wie E3, E5, M365 auf dem Screen. Mechanik und Feeling der Arcade-Vorbilder dürfen anklingen; Gegner und Welt sind **Lizenzchaos**. Visuelle Identität des **Helden** ist ausschließlich das CHAOS-Logo.

**Eine** erlaubte Vendor-Anspielung: der Donkey-Kong-Boss (Gorilla) trägt ein per Primitive gezeichnetes Microsoft-Shirt (vier farbige Quadrate + Wort `MICROSOFT`, siehe 3.B.1). Nirgends sonst.

---

## 0. Nicht verhandelbare Leitplanken

### 0.1 Betriebsziel

CHAOS Arcade ist ein **Multi-Game-Mitmach-Kabinett mit gesperrtem Titel**. Ein Messebesucher greift zum 8BitDo-Arcade-Stick, sieht das **aktuell freigeschaltete** Spiel plus dessen Top-10, startet in ≤ 3 Sekunden eine kurze Runde, gibt bei Top-10-Qualifikation **zwingend** seinen Namen ein, und das Gerät kehrt selbstständig zum Idle-Screen desselben Spiels zurück.

- Es gibt **kein** öffentliches Spielemenü, **kein** Carousel, **kein** Dateimenü, **kein** OS-UI, **kein** Beenden über sichtbare Buttons.
- Links/Rechts **wechselt das Spiel nicht**. Spielwechsel nur über die Operator-Kombination (2.3.5). Kein On-Screen-Hinweis darauf.
- Vollbild-Verlassen nur über verstecktes Operator-Hotkey (siehe 2.3.4 / 2.5).
- Jedes der sieben Spiele muss **allein mit Stick + einem Action-Button** bedienbar sein. Namenseingabe ebenfalls nur mit Stick + Action/Start.
- Median-Runde eines Erstspielers: **45–75 s** bis GAME_OVER. Zu schwer → Tempo/Dichte senken, keine Tutorials. Zu leicht → nur über Level nachziehen, nicht über neue Tasten.
- Typische Runde: **30–90 Sekunden**. Kein Spiel darf eine Einarbeitungszeit > 3 Sekunden brauchen.
- Das CHAOS-Logo ist in **allen** Spielen der **Held**. Es gibt keinen zweiten Spieler-Sprite. Braucht die Bewegung Beine oder Arme, sind das **Strichmännchen-Gliedmaßen** unter/neben dem Logo (siehe 1.7) — kein gezeichneter Körper, keine Schuhe, kein Nintendo-Kletterer.
- Gegner sind Lizenzchaos-Primitive (siehe 0.7). Sie tragen **niemals** das CHAOS-Logo.
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
- Ziel: stabil ≥ 50 FPS auf Pi 5 bei 1280×720, **in jedem** der sieben Spiele.

### 0.4 Code-Qualität

- Klare Modulstruktur (siehe 0.5). `main.py` ist der Einstieg.
- Die erste lauffähige Version darf Module bündeln, **muss** aber die genannten Klassen-/Funktionsnamen verwenden.
- Typ-Hints an allen öffentlichen Funktionen und Klassenmethoden.
- Keine Magic Numbers ohne benannte Konstanten (`config.py` + optional `games/<id>/constants.py`).
- Keine Netzwerkzugriffe, keine Telemetrie.
- UTF-8, Linux-Zeilenenden.
- Lauffähig **ohne** die drei Logo-SVGs (Fallback-Renderer je Variante ist Pflicht).
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
│   ├── frogger/
│   │   ├── lanes.py
│   │   └── mode.py
│   ├── invaders/
│   │   ├── waves.py
│   │   └── mode.py         # InvadersMode(GameMode)
│   └── breakout/
│       ├── bricks.py
│       └── mode.py         # BreakoutMode(GameMode)
├── attract.py              # Demo nur des featured Game; keine Titelrotation
├── assets/
│   ├── logo_face.svg       # Gesicht: Rauten-Augen + Lächeln (kann fehlen)
│   ├── logo_mark.svg       # Grünes C + Gesicht (kann fehlen)
│   └── logo_badge.svg      # Hex-Badge + C + Gesicht (kann fehlen)
├── data/
│   ├── highscores.json     # wird zur Laufzeit erzeugt
│   └── cabinet.json        # featured GameId; wird zur Laufzeit erzeugt
├── requirements.txt
├── setup_pi5.sh
├── .gitignore              # data/*.json, __pycache__, .venv
├── MASTER_PROMPT.md
└── README.md
```

Die erste Auslieferung darf alles in `main.py` vereinen, **muss** aber `GameId`, `GameMode`, `LogoKind`, `CabinetStore`, `HighscoreStore`, `draw_stick_hero`, `StateId.NAME_ENTRY` und die sieben Mode-Klassen (`PacmanMode`, `DonkeyKongMode`, `SnakeMode`, `BubbleShotMode`, `FroggerMode`, `InvadersMode`, `BreakoutMode`) namentlich enthalten.

### 0.6 Visuelle Identität (Arcade / CHAOS)

Shared:

- Hintergrund: tiefes Anthrazit `#0B0D10`.
- HUD: monospace, hoher Kontrast, große Zahlen (Lesbarkeit ab 1,5 m).
- Akzent: neon-cyan `#2DE2E6`, Warmweiß `#F4F1EA`, Bernstein `#FFB703`.
- Gefahr: `#FF3B3B`. Support: `#FF7AD9`, `#3BD1FF`, `#FF9F1C`.
- Kein Comic-Pac-Man-, kein Nintendo-, kein Konami-Sprite. Der Held **ist** das CHAOS-Logo, plus höchstens Strichbein/-arm.
- CHAOS-Grün der Marke (Rauten-Augen / C-Kontur) darf zusätzlich zur Neon-Palette verwendet werden; Fallback-Näherung `#7CFF3A`.

Akzente pro Spiel (nur Level-Geometrie und Gegner, nicht das Logo):

| Game | Primärakzent | Level-Look |
|---|---|---|
| PACMAN | `#2DE2E6` | Neon-Maze, dunkler Innenfill `#12161C` |
| DONKEY_KONG | `#FF9F1C` | Nieten-Träger, Leitern cyan, True-up-Rollen rot, Gorilla oben mit Microsoft-Shirt |
| SNAKE | `#2DE2E6` | Dunkelgrid, Food bernstein |
| BUBBLE_SHOT | `#3BD1FF` | Kugelfarben aus der CHAOS-Palette |
| FROGGER | `#3BD1FF` / `#FF3B3B` | Straße dunkel, Wasser cyan-dunkel, Ziele bernstein |
| INVADERS | `#FF7AD9` | Sternenfeld, Formation pink/cyan, Schüsse bernstein |
| BREAKOUT | `#FFB703` | Steinreihen = Lock-in-Klauseln, Schläger cyan |

### 0.7 Held und Gegnerwelt (Lizenzchaos)

Der Held heißt in der Fiktion **CHAOS**, der Optimizer. Er räumt Lizenzchaos auf. HUD bleibt bei `SCORE` (kein „€ eingespart“).

**Drei Logo-Varianten, eine Figur:**

| Datei | Name | Motiv | Pflicht-Einsatz |
|---|---|---|---|
| `logo_face.svg` | FACE | Neon-grüne Rauten-Augen, weißes Lächeln | Kleine Tiles, Kopf, Ball, Schiffskern |
| `logo_mark.svg` | MARK | Grünes Sechseck-C, Gesicht innen | Held mit „Körper“-Silhouette: Kanone, Schläger, Kletter-Torso |
| `logo_badge.svg` | BADGE | Weißes Hex, schwarzes C, Gesicht | Idle, Attract-Titel, Game Over, Highscore-Highlight |

Gegner-Cast (überall dieselben, nur Primitive, **ohne** CHAOS-Logo):

| Figur | Look | Rolle |
|---|---|---|
| `AUDITOR` | Rotes Klemmbrett + Monokel | Aggressiver Jäger |
| `TRUEUP` | Orangerote Rechnungsrolle | Druck, Wellen, rollende Fässer |
| `SHELFWARE` | Verstaubter grauer Schlüssel/Karton | Langsam, wertvoll |
| `SKUWIRR` | Bunter Etikettenstapel | Unberechenbar |
| `LOCKIN` | Dunkles Schloss-Rechteck | Wand, 2-Hit-Stein, Rand |
| `RENEWAL` | Kalender auf Rädern | Fahrzeuge, rollende Hazard |
| `NOTICE` | Papierflieger / Briefbombe | Gegner-Projektile |
| `KLAUSEL` | Kleingedruckt-Ziegel | Invaders-Reihen, Breakout-Steine |
| `AE` | Fliegende Aktentasche | Bonus-UFO |
| `TENANT` | Wolken-Floß | Frogger-Fluss |

Idle-Mechanikzeile (deutsch, max. 28 Zeichen):

| Game | Zeile |
|---|---|
| PACMAN | `ISS DAS SHELFWARE` |
| DONKEY_KONG | `KLIMM ZUM VERTRAG` |
| SNAKE | `FRISS UNGENUTZTE SEATS` |
| BUBBLE_SHOT | `SORTIER DIE SKUS` |
| FROGGER | `QUER DURCHS RENEWAL` |
| INVADERS | `SCHIESS DEN AUDIT AB` |
| BREAKOUT | `BRICH DEN LOCK-IN` |

SKU-Typen auf dem Screen nur als Gattung: `BASIS`, `PREMIUM`, `FRONTLINE`, `ADDON`, `SANDBOX`. Keine Microsoft-Produktnamen.

---

## 1. Asset-Pipeline & SVG-Rendering

### 1.1 Quelle und Verträge

Enum `LogoKind = FACE | MARK | BADGE`.  
`LogoAsset.load(kind: LogoKind, path: Path, size: int) -> pygame.Surface`.

Jedes SVG gilt als **quadratisch normiert**. Nicht-quadratische ViewBox: proportional fitten, zentrieren, niemals strecken.

Rastergrößen, **einmal** beim Boot cachen (`(kind, size)`):

| Cache-Key | Kind | Größe | Verwendung |
|---|---|---|---|
| `logo_hero` | BADGE | 160 | SELECT / Titel / GAME OVER |
| `logo_tile` | FACE | `TILE_SIZE - 4` (Default 28) | Pac-Man, Snake-Kopf, Frogger-Kopf |
| `logo_dk` | MARK | 36 | Donkey-Kong-Torso (Beine/Arme = Strich, 1.7) |
| `logo_cannon` | MARK | 48 | Bubble-Shot-Kanone |
| `logo_bubble` | FACE | 28 | Bubble-Kugel, Breakout-Ball (getintet) |
| `logo_snake_body` | FACE | 24 | Snake-Körper (getintet, 70 % Alpha) |
| `logo_ship` | MARK | 36 | Invaders, Facing UP, keine Beine |
| `logo_paddle` | MARK | 40 | Breakout, zentriert auf dem Schläger-Rect |
| `logo_nest` | FACE | 20 | Frogger-Nest gefüllt |

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

**Stufe C — geometrischer Fallback** `render_fallback_logo(kind, size)` — ahmt die echte Marke nach, kein Pac-Man-Kuchen:

Gemeinsames Gesicht (FACE-Kern):

- Zwei Rauten-Augen, Fill `#7CFF3A`, Breite `size * 0.16`, Abstand der Mittelpunkte `size * 0.28`, sitzen im oberen Drittel.
- Lächeln: weiße Linse/Bogen, Stroke `size * 0.07`, Öffnung nach oben, Breite `size * 0.42`.

MARK zusätzlich: Sechseck-C, Stroke `#7CFF3A`, Dicke `size * 0.10`, Öffnung nach **rechts**, Gesicht zentriert in der Öffnung.

BADGE zusätzlich: äußeres weißes Sechseck-Fill, darin schwarzes C wie MARK, Gesicht mit grünen Augen und dunklem Lächeln.

`LogoAsset.load` wirft **keine** Exception nach außen. Fehlt eine Datei, fällt nur diese Variante auf Stufe C, die anderen bleiben geladen.

### 1.3 Richtungs-Transformation

Einmal vier Richtungs-Surfaces pro Größe cachen. Basis: Logo schaut nach **rechts**. Korrektur nur über `LOGO_BASE_FACING`.

| Richtung | Transformation |
|---|---|
| RIGHT | unverändert |
| LEFT | `flip(base, True, False)` Default (`LOGO_LEFT_MODE = "flip"`) |
| UP | `rotate(base, 90)` + `_fit_square` |
| DOWN | `rotate(base, -90)` + `_fit_square` |

- Niemals `rotozoom` pro Frame, niemals SVG neu parsen.
- `tint_surface(surf, color)` einmalig für Snake-Körper, Bubble-Farben, Breakout-Ball. Gegner werden **nicht** aus dem Logo getintet.

### 1.4 Nutzungsregeln pro Spiel

| Game | Logo (Held) | Gliedmaßen |
|---|---|---|
| PACMAN | `logo_tile` FACE + Facing-Cache | keine — schwebt |
| DONKEY_KONG | `logo_dk` MARK, Facing L/R; auf Leiter kein Kopfstand | **Strichbeine + Stricharme** (1.7), immer |
| SNAKE | Kopf FACE; Körper FACE getintet `#2DE2E6` | keine |
| BUBBLE_SHOT | Kanone MARK, 2°-Winkel-Cache; Kugel FACE getintet | keine |
| FROGGER | `logo_tile` FACE, Idle UP | **Strichbeine**, 2-Frame-Hop |
| INVADERS | `logo_ship` MARK, Facing UP | keine — fliegt |
| BREAKOUT | Schläger MARK mittig; Ball FACE | keine |

Bubble-Shot-Rotation: Winkel-Cache beim Start in 2°-Schritten, **kein** per-frame `rotozoom` auf das SVG.

Das Logo darf **nicht** als Boss, Geist, Fass, Auto, Invader oder Stein erscheinen. Nur der vom Spieler gesteuerte Held (plus seine eigenen Projektile/Körpersegmente/Nest-Markierung).

### 1.5 Logging

```
[assets] FACE loaded via cairosvg: assets/logo_face.svg
[assets] MARK load failed (...), using fallback geometry
```

### 1.7 Strichmännchen-Gliedmaßen

Funktion `draw_stick_hero(surf, logo_surf, anchor, facing, pose) -> None`.

Das Logo bleibt Kopf **und** Torso. Striche sind nur Arme und Beine, zur Laufzeit gezeichnet (nicht ins SVG einbrennen — sonst kein Walk-Cycle).

```
STICK_COLOR = #2DE2E6
STICK_WIDTH = 3          # 2 px unter size 28
LEG_LEN = logo_h * 0.55
ARM_LEN = logo_h * 0.45
```

| `pose` | Beine | Arme |
|---|---|---|
| `IDLE` | beide senkrecht, 8° gespreizt | am Körper, 15° |
| `WALK_A` / `WALK_B` | im Wechsel ±28° (2 Frames, 8 Hz am Boden) | gegenläufig ±20° |
| `JUMP` | beide leicht nach hinten 25° | beide nach vorn 30° |
| `CLIMB` | gestaffelt ±18° vertikal | nach oben an die Leiter, 70° |
| `HOP` | beide nach hinten 40° für 80 ms, dann IDLE | optional kurz nach vorn |

Regeln:

- Ansatz Beine: Unterkante-Mitte des Logo-Rects. Ansatz Arme: linke/rechte Seitenmitte.
- Keine Füße, keine Hände, keine Gelenkkugeln größer als 3 px.
- Kein zweiter Kopf, kein Strich-Rumpf durch das Logo.
- Logo niemals auf den Kopf drehen, um „Beine oben“ zu simulieren.
- Nur DK und Frogger rufen `draw_stick_hero` auf. Alle anderen Spiele: nur Logo.

### 1.8 Abhängigkeiten

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
    INVADERS: InvadersMode,
    BREAKOUT: BreakoutMode,
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
- Eine Zeile Mechanik des featured Game — verbindlich die Tabelle in 0.7.
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
    "FROGGER": [],
    "INVADERS": [],
    "BREAKOUT": []
  }
}
```

`HighscoreStore.add(game_id, name, score, level) -> int` gibt den 1-basierten Rang zurück (0 = nicht aufgenommen).

- Pro `GameId` maximal 10 Einträge, sortiert `score` desc, dann `ts` desc.
- `name` ist Pflicht: 3–8 Zeichen aus `[A-Z0-9-]`. Fehlt oder ungültig → **kein Write**.
- Atomar: `highscores.json.tmp` + `os.replace`.
- Corrupt → leere Listen für alle sieben Keys, Rebuild beim Write.
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
- `1`…`7`: stille Direktwahl des featured Game (Dev/Operator, Katalogreihenfolge), erlaubt in `GAME_SELECT`, `ATTRACT_MODE` und in `GAME_OVER` **ohne** Qualifikation — nicht in `PLAYING` / `NAME_ENTRY` / qualifiziertem `GAME_OVER`.

#### 2.3.5 Operator-Spielwechsel (verbindlich)

Öffentliches Links/Rechts **darf das Spiel nicht wechseln**. Nur wer die Kombination kennt, schaltet den Kabinett-Titel um.

**Modifier (gehalten):**

| Quelle | Modifier |
|---|---|
| Tastatur | `K_LSHIFT` |
| 8BitDo / Gamepad | Button **6 oder 8** (Select) **oder** Button **7 oder 9** (Start), gehalten. **Nicht** Button 0/1 (Action). |

**Schaltgeste:** Modifier gehalten + `Left`/`Right` Edge → `featured` ± 1, Wrap Pac-Man ↔ Breakout. Sofort `CabinetStore.save`. Titel + Top-10 wechseln in derselben Frame-Logik.

Zusätzlich Dev: Tasten `1`…`7` (siehe 2.3.4).

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

#### 2.3.7 Namensfilter

`config.NAME_BLOCKLIST`: kurze, interne Substring-Liste (casefold). Treffer → kein Write, Cursor bleibt in `NAME_ENTRY`, Hinweis `NAME UNGÜLTIG` 1,2 s. Die Liste steht **nicht** in README oder HUD. Leere Liste ist unzulässig — mindestens ein Platzhalter-Eintrag im Code, echte Wörter darf der Operator in `config.py` pflegen.

#### 2.3.8 Kiosk-Härtung (Pi 5 / 8BitDo)

Pflichtbestandteil von `setup_pi5.sh` und der Shell, nicht optional „später“:

- systemd-Unit `chaos-arcade.service`: `Restart=always`, `RestartSec=2`, WorkingDirectory = Repo, `ExecStart=/usr/bin/python3 main.py`. Watchdog: Prozess muss mindestens alle 10 s ein `WATCHDOG=1` schreiben **oder** die Unit kommt ohne sd_notify aus und verlässt sich auf Restart bei Exit ≠ 0. Beides ist zulässig; Absturz darf das Kabinett nicht schwarz lassen.
- Screen-Blank und DPMS aus (`xset s off`, `xset -dpms` bzw. Wayland-Äquivalent). `pygame.mouse.set_visible(False)` bleibt.
- HDMI als Audio-Default, Mixer-Fehler weiter ignorieren.
- 8BitDo DIY Kit: Standard-HID, nicht Switch-Modus. Skript dokumentiert nur „im OS einmalig pairen, dann reboot“ — kein Runtime-Bluetooth-Scan im Game.
- Burn-in-Schutz: nach `BURN_IN_IDLE_SECONDS = 180` im Select/Attract-Loop HUD und Top-10 alle 30 s um ±2 px versetzen. Kein Dimmen unter Lesbarkeit.
- Kein Netzwerkstack im Spielprozess.

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
| INVADERS | L/R gehalten bewegen, U/D ignoriert | Schuss (Edge), max. 1 Kugel, Cooldown 0.28 s |
| BREAKOUT | L/R gehalten Schläger, U/D ignoriert | Ball starten (Edge), nur solange der Ball klebt |

### 2.5 Robustheit

- `SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS=1` vor `pygame.init()`.
- Mixer-Fehler → `audio_enabled = False`.
- Font: DejaVu Sans Mono Bold falls vorhanden, sonst `Font(None, size)`.
- Uncaught Exception: loggen, 2 s warten, hart `GAME_SELECT`. Ein Game-Crash darf die anderen sechs nicht töten — `GameMode.update` in try/except der Shell.

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
- 3 Leben, sofern das Spiel Leben hat (Snake: 1 Leben / Sofort-Out, dann GAME_OVER — siehe 3.C). Invaders und Breakout: 3 Leben.
- Level-Steigerung erhöht Tempo oder Dichte, nie die Steuerung umbauen.
- Held = CHAOS-Logo (± Strichgliedmaßen). Gegner = Lizenzchaos-Cast aus 0.7, nie das Logo.

---

### 3.A PACMAN

Vertragsflure statt Geisterhaus-Märchen: CHAOS frisst ungenutzte Seats (`Dots`), Optimize (`Power`) macht Auditoren kurz `COMPLIANT`. KI und Zahlen bleiben der Pac-Man-Vertrag.

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
Zeichnung: Pygame-Primitives, **kein** CHAOS-Logo.

| KI-Name | Sichtname | Look |
|---|---|---|
| BLINKY | AUDITOR | rotes Klemmbrett, Monokel |
| PINKY | TRUEUP | orangerote Rechnungsrolle |
| INKY | SKUWIRR | Etikettenstapel, CHAOS-Palette |
| CLYDE | SHELFWARE | grauer Schlüsselkarton |

FRIGHTENED = `COMPLIANT`: cyan, flieht. EATEN = leeres Klemmbrett-Augenpaar zur Basis.

#### 3.A.5 Player

3 Leben, INVULN 2.0 s nach Respawn. Kollision Kreis-Radius `TILE_SIZE * 0.35`. FACE-Logo, Facing-Cache, **keine** Beine.

---

### 3.B DONKEY KONG

Messe-Plattformer, **eine** kompakte Vertragsturm-Szene (kein 4-Board-Original). Gefühl: unten starten, oben Optimierungs-Siegel, True-up-Rollen weichen, Leitern nutzen, springen. Held = MARK-Logo auf Strichbeinen.

#### 3.B.1 Bühne

- 6 horizontale Träger (Girders), leicht gegenläufig geneigt (±4° optisch, Kollision als Achsen-Segmente).
- Pro Träger 1–2 Leitern, die den nächsthöheren Träger verbinden. Mindestens ein durchgehender Pfad nach oben.
- Oben links oder mitte: Boss `GorillaActor` — ein **Gorilla**, nicht steuerbar, **kein** CHAOS-Logo, kein Nintendo-DK-Sprite. Nur Pygame-Primitive.
  - Körper: dunkles Braun `#5A3A22`, Kopf-Ellipse, zwei Ohren, lange Arme. Sitz-/Standpose auf dem obersten Träger, Breite ca. 88 px, Höhe ca. 96 px.
  - **Microsoft-Shirt** (Pflicht): helles Rechteck auf dem Torso (`#F4F1EA`, ca. 44×28 px). Darauf **vier Quadrate** in den Microsoft-Fensterfarben, 2×2, je 9 px, Gap 2 px:
    oben links `#F35325`, oben rechts `#81BC06`, unten links `#05A6F0`, unten rechts `#FFBA08`.
    Darunter zentriert der Schriftzug `MICROSOFT` in DejaVu Sans Mono, 10 px, `#0B0D10`.
  - Keine heruntergeladene Microsoft-Grafik, keine Word-/Azure-Bildmarke, kein Windows-Flaggen-SVG. Nur diese vier Rects + Text.
  - Wurf-Pose: rechter Arm hebt sich 200 ms, dann TRUEUP-Rolle. Idle: leichtes 1 Hz-Atmen (ScaleY 0.98–1.02, nur Körper, Shirt sitzt fest).
- Oben rechts: Ziel `GOAL` (Optimierungs-Siegel, bernstein). Berühren = Level-Clear + 500 Punkte + nächste, schnellere Runde.
- Unten: Player-Spawn.

Interne Playfield-Größe: 960×560, zentriert unter HUD.

#### 3.B.2 Physik (arkade, nicht Box2D)

- Laufen: 180 px/s. Gravitation 2200 px/s², Terminal 720 px/s.
- Sprung: Edge-Action, nur wenn `grounded`. `jump_v = -620` px/s.
- Leiter: wenn `dy < 0` und Overlap mit Leiter-Rect ≥ 40 % der Spielerbreite → Climb-State, 140 px/s vertikal, Gravitation aus. `dy > 0` steigt herab. Horizontal auf Leiter gedämpft (0).
- Kein Double-Jump, kein Luft-Steuern über 35 % der Boden-Speed hinaus.
- Träger-Kollision: Strichfüße gegen Oberkante. Durch Leiternlöcher darf der Spieler fallen, wenn nicht im Climb-State.

#### 3.B.3 Fässer und Gefahr

- `GorillaActor` wirft alle `BARREL_INTERVAL` (1.6 s Level 1, −0.12 s/Level, min 0.7 s) eine **TRUEUP-Rolle**.
- Rollen folgen Trägern (rollen in Neigungsrichtung), fallen am Ende eine Ebene tiefer, despawnen unten.
- 15 % Chance: Rolle wird zum **Fall-Notice** (vertikal, schneller) — telegraphiert durch kürzeres Rect.
- Kollision Spieler/Rolle: Kreis-Kreis, außer während Sprung **über** die Rolle (Strichfuß-y < Rollen-Oberkante − 4 px) → +100 Punkte, kein Schaden.
- 3 Leben. Tod: Freeze 1.2 s, Respawn unten. 0 Leben → GAME_OVER.
- Optional ab Level 2: ein `AUDITOR` auf dem untersten Träger, KI = läuft auf den Spieler zu, kehrt an Leiter/Rand um. Primitive, kein Logo.

#### 3.B.4 Steuerung und Logo

- LEFT/RIGHT: Facing + Lauf, Pose `WALK_A`/`WALK_B`.
- UP/DOWN: Leiter, Pose `CLIMB`.
- Action: Sprung, Pose `JUMP`.
- `draw_stick_hero` jedes Frame. Logo nicht auf den Kopf drehen. Auf Leitern: letztes L/R-Facing behalten.

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

- Kopf: FACE `logo_tile[facing]`, keine Beine.
- Körper: Kette FACE `logo_snake_body`, Alpha 220 → 90 zum Schwanz.
- Food: `SHELFWARE`-Token (grauer Schlüssel-Rect oder Mini-FACE getintet bernstein), pulsiert 2 Hz ±8 %.

---

### 3.D BUBBLE SHOT

Aim-and-match, Puzzle-Bobble-Feeling, CHAOS-Farben. Kein originaler Bobble-Sprite.

#### 3.D.1 Spielfeld

- Hex- oder Offset-Row-Grid: `BUBBLE_COLS = 10`, sichtbare Reihen max. 12, Kugel-Durchmesser 36 px.
- Decke fest (jährlicher True-up). Neue Reihe schiebt alle `CEILING_EVERY_SHOTS = 6` Schüsse nach unten (Level 1), ab Level 3 alle 5, ab Level 5 alle 4.
- Bodenlinie 80 px über dem Fußbereich (Budget-Boden): berührt eine Kugel die Linie → GAME_OVER (nach kurzem Flash).
- Kanone mittig unten. Held = MARK-Logo als Kanonenkopf, Lauf = cyan Rechteck. Keine Beine.

#### 3.D.2 Zielen und Schuss

- Winkelbereich **−75° … +75°** (0° = senkrecht nach oben).
- LEFT/RIGHT: `±90°/s` analog gehalten. UP/DOWN: Raster ±8°.
- Action-Edge: feuert die **aktuelle** Kugel. Nächste Kugel liegt sichtbar rechts der Kanone (Preview).
- Flug: 720 px/s gerade, Reflektion **nur** an linker/rechter Wand (`vx = -vx`). Keine Decken-Reflektion — Kontakt Decke/Kugel = Snap ins Grid.
- Genau **eine** fliegende Kugel gleichzeitig.

#### 3.D.3 Farben und Match

Farben = SKU-Gattungen (max. 4 auf Level 1, 5 ab Level 3), ohne Microsoft-Namen:

| Farbe | Gattung |
|---|---|
| `#2DE2E6` | BASIS |
| `#FF3B3B` | PREMIUM |
| `#FF7AD9` | FRONTLINE |
| `#FFB703` | ADDON |
| `#3BD1FF` | SANDBOX |

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

Raster-Queren durchs Renewal: Straße, Mittelstreifen, Cloud-Fluss, 5 Kostenstellen. Held = FACE-Logo auf Strichbeinen.

#### 3.E.1 Layout (13 Reihen × 15 Spalten)

Von unten nach oben:

0. Safe Home (Startreihe, Player-Spawn Mitte)  
1–4. Straße: 4 Lanes, Fahrzeuge  
5. Safe Median  
6–9. Wasser: 4 Lanes, Holz/Schildkröten  
10. Bank  
11. 5 Nester (`HOME` / Kostenstellen), getrennt durch Mauern  
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
- Autos = `RENEWAL` (Kalender-Rects), 2–3 Stück, Lücken immer ≥ 2 Tiles bei Level 1.
- Fluss: `TENANT`-Flöße 2–4 Tiles; ab Level 2 tauchen abgekündigte SKUs alle 3 s für 1.0 s.
- Spieler auf Floater erbt `vx` der Lane (pixelgenau zwischen Hops, gerastert beim nächsten Hop).
- Wrap: Hazards verlassen links und kommen rechts wieder (und umgekehrt).
- Level+1 wenn alle 5 Nester gefüllt: Speeds `* 1.12`, eine zusätzliche Auto-Lane-Dichte, Timer härter.

#### 3.E.4 Leben, Zeit, Score

- 3 Leben. Tod: Respawn Startreihe, aktueller Nest-Fortschritt bleibt.
- Timer pro Versuch: 20 s → 0 = Tod. Reset bei erfolgreichem Nest.
- Nest erreichen: +200 + `int(remaining_s)*10`. Vorwärts-Hop +10. Alle 5 Nester: +500 und Level-Up, Nester leeren.

#### 3.E.5 Darstellung

- Player: FACE `logo_tile[facing]` plus `draw_stick_hero(..., HOP|IDLE)` — Beine beim Hop 80 ms nach hinten.
- Autos: `RENEWAL`-Kalender, neon-rot/pink, keine Sprite-Roms.
- Flöße: `TENANT`, dunkles Cyan-Braun-Rechteck.
- Nester: bernstein-Mulde; gefüllt = FACE `logo_nest` 20 px (Held sitzt, keine Beine im Nest).

---

### 3.F INVADERS

Messe-Shmup: Audit-Welle. Gefühl Space Invaders, keine originalen Sprite-Roms, keine Galaga-Challenging-Stage. Held = MARK-Logo als Schiff, **ohne** Beine.

#### 3.F.1 Feld

Playfield 720×560, zentriert unter dem HUD. 40 px Seitenrand. Spieler-Schiff auf `y = play_bottom - 40`. Kein Wrap — am Rand stoppen (Messe: klare Grenze).

#### 3.F.2 Spieler

- LEFT/RIGHT gehalten: 320 px/s.
- Action-Edge: eine Kugel nach oben, 520 px/s. Maximal **eine** eigene Kugel gleichzeitig. Zusätzlicher Cooldown 0.28 s.
- Treffer durch Bomben oder Kontakt mit Invader: Leben −1, Freeze 1.2 s, INVULN 2.0 s, Formation bleibt.
- 0 Leben → GAME_OVER.
- Logo: `logo_ship` MARK, Facing UP fest, keine Gliedmaßen. Schüsse = Primitive, nicht das Logo.

#### 3.F.3 Formation

- Level 1: 5 Reihen × 8 Spalten, Zelle 36 px, Abstand 8 px.
- Farben zeilenweise: unten `SHELFWARE`, dann `ADDON`/`SKUWIRR`, oben `KLAUSEL`/`AUDITOR`.
- Blockbewegung: 40 px/s Level 1, am Rand umkehren und 12 px sinken. Tempo `* 1.10` je Welle, plus `* 1.04` je getötetem Invader (klassische Beschleunigung).
- Globaler Bomben-Takt: alle 1.2 s Level 1, −0.08 s/Welle, min 0.45 s. Zufällige lebende untere Kante schießt. Bombe 220 px/s nach unten, Primitive.
- Unterkante der Formation erreicht Spieler-y → sofort GAME_OVER (alle Restleben verloren).
- Welle leer: +500, nächste Welle (max. 6 Reihen). UFO = `AE` (Aktentasche) alle 12 s oben durch, 150 Punkte, 180 px/s, **nur** Primitive — kein CHAOS-Logo.

#### 3.F.4 Scoring

| Event | Punkte |
|---|---|
| Invader Reihe 1 (unten) … 5 (oben) | 10 / 20 / 30 / 40 / 50 |
| UFO | 150 |
| Welle frei | 500 |

#### 3.F.5 Darstellung

- Invader: Rechtecke/Diamanten als Klemmbrett/Klausel, 2 px Outline, kein Copyright-Sprite, kein Logo.
- Hintergrund: 40 statische Sterne (einmal generiert, Position + Parallax 8 px — brennt nicht ein).
- Attract: Schiff pendelt und schießt deterministisch.

---

### 3.G BREAKOUT

Schläger unten, Ball, Lock-in-Wand oben. Gefühl Breakout, keine Arkanoid-Powerups, keine ROM-Sprites. Held = MARK auf dem Schläger, FACE als Ball. Keine Beine.

#### 3.G.1 Feld

Playfield 800×560, zentriert. Wände links/rechts/oben 12 px cyan. Unten offen.

#### 3.G.2 Schläger und Ball

- Schläger: 96×18 px, 420 px/s, LEFT/RIGHT gehalten, stoppt am Innenrand. `logo_paddle` zentriert auf dem Rect.
- Ball: Radius 8 px, `logo_bubble` 20 px. Start klebt auf dem Schläger, bis Action-Edge ihn startet (Anfang `vy < 0`, `vx` aus Schläger-Offset).
- Startspeed 360 px/s, `* 1.04` je zerstörtem Stein, Maximum 620 px/s.
- Kollision Schläger: Winkel aus Trefferoffset, max. ±55° gegen die Senkrechte, `|vy|` bleibt aufwärts. Nie flach horizontal.
- Wand: `vx` bzw. `vy` invertieren. Decke spiegelt `vy`.
- Ball verlässt unten: Leben −1, Ball klebt wieder. 0 Leben → GAME_OVER.

#### 3.G.3 Steine

- Level 1: 6 Reihen × 10 Spalten, Stein 72×22, Gap 4 px, oberer Offset 24 px.
- Reihenfarben CHAOS-Palette. Punkte oben → unten: 30 / 25 / 20 / 15 / 10 / 10.
- Keine unzerstörbaren Steine auf Level 1. Ab Level 2: genau 4 graue 2-Hit-`LOCKIN`-Steine (Outline dick, Schloss-Kerbe).
- Feld leer: +500, nächste Wand (eine Reihe mehr, max. 8; Speed-Reset auf `360 * 1.06^(level-1)`).

#### 3.G.4 Scoring und Leben

- 3 Leben. Steinpunkte + Clear 500. Kein Zeitbonus (Tempo ist die Uhr).
- Keine Powerups (Multiball, Laser, Enlarge) — eine Taste, eine Regel.

#### 3.G.5 Darstellung

- Steine: `KLAUSEL`-Rects + 2 px Outline, kein Logo.
- Attract: Schläger folgt dem Ball deterministisch mit 70 % Speed (darf verlieren und resetten, kein Score).

---

## 4. Implementierungsauftrag

Reihenfolge **zwingend** (jedes Game nach Shell spielbar committen, nicht sieben halbfertige):

1. Shared Shell: Display, Input, LogoAsset, Highscore inkl. Name, CabinetStore, GAME_SELECT-Idle + Top-10-Tafel, Operator-Switch, ATTRACT-Gerüst (nur featured), GAME_OVER, NAME_ENTRY, Namensfilter, Burn-in-Shift.
2. `PacmanMode` vollständig (Abnahme §5.A). Featured-Default = PACMAN.
3. `SnakeMode` (schnellster zweiter Titel). Operator kann darauf schalten, sobald spielbar.
4. `FroggerMode`.
5. `InvadersMode`.
6. `BreakoutMode`.
7. `BubbleShotMode`.
8. `DonkeyKongMode`.
9. Attract spielt **nur** das featured Game. Ein unfertiger Titel darf **nicht** per Operator erreichbar sein. Zielstand: alle sieben fertig und per Kombo wählbar. Kein `Coming Soon`, kein öffentliches Carousel. Kein achter Titel.

Weitere Regeln:

1. `requirements.txt` + `setup_pi5.sh` für Pi 5 / Bookworm inkl. systemd-Unit, DPMS-aus, 8BitDo-Pairing-Hinweis.
2. README: `python3 main.py`, `CHAOS_WINDOWED=1`, kurze Spielübersicht, **ohne** die Operator-Kombo preiszugeben (die steht nur hier im Prompt).
3. Ohne die drei Logo-SVGs starten alle sieben mit Fallback-Gesicht/C/Badge.
4. Mit den SVGs ist CHAOS in jedem Titel der Held (siehe 1.4). DK und Frogger haben Strichbeine; Gegner nie das Logo.
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
- [ ] Tasten `1`…`7` schalten featured still; unfertige Titel sind nicht erreichbar.
- [ ] Namensfilter blockt `NAME_BLOCKLIST` ohne Write.
- [ ] `setup_pi5.sh` legt Restart-Unit an und schaltet Screen-Blank ab. Nach 180 s Idle ±2 px Burn-in-Shift.
- [ ] Start/Action lädt das featured Spiel; Game-Over kehrt zum Idle **desselben** Titels zurück (außer Operator hat danach umgeschaltet).
- [ ] Qualifizierter Score öffnet NAME_ENTRY; Absenden erst ab 3 Zeichen; Write nur mit Name. Timeout 20 s verwirft den Score.
- [ ] Unqualifizierter Score (0 oder unter Platz 10 bei voller Liste): kein NAME_ENTRY, kein Write.
- [ ] Top-10-Tafel mit Name+Score ist in SELECT, ATTRACT, GAME_OVER, NAME_ENTRY sichtbar; in PLAYING nicht.
- [ ] 12 s Idle → Attract **desselben** Titels (keine Titelrotation); Input → SELECT.
- [ ] 30 s Idle in PLAYING → SELECT, kein Highscore-Write.
- [ ] Highscores getrennt pro Game, inkl. Name, überleben Neustart; Legacy-`entries` → PACMAN mit `name = "---"`.
- [ ] Logo-Pipeline FACE/MARK/BADGE, cairosvg → pygame → Fallback, Logs auf stdout.
- [ ] CHAOS-Logo ist in jedem Titel der Held. Gegner nie das Logo. Nur DK und Frogger haben Strichbein/-arm.
- [ ] 8BitDo D-Pad, Analog, A/Start/Select und Keyboard parallel; Action ist Edge; Start gehalten + Richtung = Operator, nicht Spielstart.
- [ ] Fullscreen-Kiosk, Cursor aus, Shift+Q beendet.
- [ ] ≥ 50 FPS in jedem aktiven Spiel.

### 5.A Pac-Man

- [ ] Richtungs-Logo, 4 Geister-Persönlichkeiten, Frightened/Eaten, Dots, Power, Tunnel, 3 Leben, Level-Clear.

### 5.B Donkey Kong

- [ ] Laufen, Leitern, Sprung, True-up-Rollen mit Träger-Logik, Ziel oben, Zeitlimit, Skip-Punkte, 3 Leben. Held = MARK + Strichbein. Oben ein Gorilla mit Primitive-Microsoft-Shirt (4 Quadrate + `MICROSOFT`), ohne CHAOS-Logo, ohne offizielle MS-Datei.

### 5.C Snake

- [ ] Queue ohne 180°-Selbstkill, Wachstum, Speed-up, Wand = Tod, Kopf = Logo.

### 5.D Bubble Shot

- [ ] Winkeln, Schuss, Wandreflex, Grid-Snap, Match-≥3, Fallgruppen, Aim-Linie, Ceiling-Push, Boden = Out.

### 5.E Frogger

- [ ] Edge-Hops, Renewal-Autos, Tenant-Flöße, Wasser-Tod, 5 Kostenstellen, Timer, Level nach Full-Home. Held = FACE + Strichbein.

### 5.F Invaders

- [ ] L/R-Schiff, ein Schuss, Formation mit Kanten-Drop und Tempo-up, Bomben, 3 Leben, Welle-Clear, Bodenkontakt = Out.

### 5.G Breakout

- [ ] Schläger, klebender Startball, Winkel über Trefferoffset, Steinwand, Speed-up, 3 Leben, kein Powerup.

---

## 6. Self-Check vor dem Commit der Implementierung

1. Existieren `GameMode` und sieben Mode-Klassen, auch wenn noch in `main.py` gebündelt?
2. Eine Shared-Quelle für Display/Input/Logo/Highscore/Cabinet?
3. Werden FACE/MARK/BADGE niemals pro Frame gerastert — auch nicht für Bubble-Winkel (Cache!)? Werden Strichbeine zur Laufzeit gezeichnet, nicht ins SVG gebrannt?
4. Sind Diagonalen in Pac-Man/Snake/Frogger unmöglich? (DK: in der Luft begrenztes Strafen erlaubt, kein 8-Wege-Run. Invaders/Breakout: nur L/R.)
5. Kann das Kabinett 2 Minuten ohne Input im Select/Attract-Zyklus **desselben** featured Game allein laufen?
6. Sind `data/highscores.json` und `data/cabinet.json` gitignored?
7. Gibt es **kein** öffentliches Carousel, keinen achten Titel und keinen `Coming Soon`-Slot? Ist Spielwechsel ausschließlich die Operator-Kombo?
8. Crash in einem Mode fängt die Shell und kehrt zu SELECT zurück?
9. Wird kein Highscore ohne gültigen Namen (3–8, `[A-Z0-9-]`) oder mit Blocklist-Treffer geschrieben?
10. Ist die Operator-Kombo nirgends im HUD oder in der README erklärt?
11. Startet die systemd-Unit das Spiel nach einem Crash von selbst neu?
12. Ist CHAOS in jedem Titel der einzige Held? Tragen Gegner nirgends das Logo? Haben nur DK und Frogger Strichgliedmaßen?

Ende des Master-Prompts. Dieses Dokument ist die einzige Wahrheitsquelle für die Code-Generierung.
