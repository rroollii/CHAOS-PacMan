#!/usr/bin/env bash
# CHAOS Arcade — Raspberry Pi 5 / Bookworm kiosk installer
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
USER_NAME="${SUDO_USER:-$USER}"
HOME_DIR="$(getent passwd "$USER_NAME" | cut -d: -f6)"
UID_NUM="$(id -u "$USER_NAME")"
SERVICE_PATH="/etc/systemd/system/chaos-arcade.service"

echo "[setup] Installing system packages…"
sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
  python3 python3-venv python3-pip \
  libcairo2 libcairo2-dev libgdk-pixbuf-2.0-0 libffi-dev \
  libxml2 libpango-1.0-0 shared-mime-info \
  fonts-dejavu-core \
  bluetooth bluez blueman \
  x11-xserver-utils unclutter \
  joystick evtest

echo "[setup] Python venv…"
python3 -m venv --system-site-packages "$ROOT/.venv"
"$ROOT/.venv/bin/pip" install --upgrade pip
if ! "$ROOT/.venv/bin/pip" install -r "$ROOT/requirements.txt"; then
  echo "[setup] WARNING: pip extras failed (cairosvg is optional). Fallback geometry still works."
fi

mkdir -p "$ROOT/data"
chown -R "$USER_NAME:$USER_NAME" "$ROOT/data" "$ROOT/.venv" || true

echo "[setup] Disable screen blank / DPMS (X11)…"
mkdir -p "$HOME_DIR/.config/autostart"
cat > "$HOME_DIR/.config/autostart/chaos-dpms.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=CHAOS disable blank
Exec=sh -c "xset s off; xset -dpms; xset s noblank; unclutter -idle 0.1 -root"
X-GNOME-Autostart-enabled=true
EOF

echo "[setup] Disable idle blank (Wayfire)…"
mkdir -p "$HOME_DIR/.config"
if [ -f "$HOME_DIR/.config/wayfire.ini" ]; then
  if ! grep -q "^\\[idle\\]" "$HOME_DIR/.config/wayfire.ini"; then
    printf "\\n[idle]\\ndpms_timeout = -1\\n" >> "$HOME_DIR/.config/wayfire.ini"
  fi
else
  cat > "$HOME_DIR/.config/wayfire.ini" <<'EOF'
[idle]
dpms_timeout = -1
EOF
fi

echo "[setup] Disable idle blank (labwc)…"
mkdir -p "$HOME_DIR/.config/labwc"
cat > "$HOME_DIR/.config/labwc/autostart" <<'EOF'
wlr-randr --output HDMI-A-1 --on || true
EOF
if [ ! -f "$HOME_DIR/.config/labwc/rc.xml" ]; then
  cat > "$HOME_DIR/.config/labwc/rc.xml" <<'EOF'
<?xml version="1.0"?>
<labwc_config>
  <power>
    <offTimeout>0</offTimeout>
  </power>
</labwc_config>
EOF
fi

echo "[setup] HDMI as default audio sink (best effort)…"
if command -v pactl >/dev/null 2>&1; then
  HDMI_SINK="$(pactl list short sinks 2>/dev/null | awk '/hdmi|HDMI/{print $2; exit}')" || true
  if [ -n "${HDMI_SINK:-}" ]; then
    pactl set-default-sink "$HDMI_SINK" || true
  fi
fi

chown -R "$USER_NAME:$USER_NAME" "$HOME_DIR/.config"

echo "[setup] systemd unit…"
sudo tee "$SERVICE_PATH" >/dev/null <<EOF
[Unit]
Description=CHAOS Arcade kiosk
After=graphical.target bluetooth.service
Wants=bluetooth.service

[Service]
Type=simple
User=$USER_NAME
WorkingDirectory=$ROOT
Environment=DISPLAY=:0
Environment=WAYLAND_DISPLAY=wayland-0
Environment=XDG_RUNTIME_DIR=/run/user/$UID_NUM
Environment=SDL_AUDIODRIVER=alsa
NotifyAccess=all
ExecStart=$ROOT/.venv/bin/python3 $ROOT/main.py
Restart=always
RestartSec=2
WatchdogSec=15
TimeoutStopSec=5

[Install]
WantedBy=graphical.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable chaos-arcade.service

echo
echo "[setup] 8BitDo pairing (once, in the OS — not inside the game):"
echo "  1. Power the DIY Kit. Hold Start (or the pair button) until the LED blinks."
echo "  2. Use standard HID / X-input / Android / Windows mode. Do NOT use Switch mode."
echo "  3. bluetoothctl:"
echo "       power on"
echo "       agent on"
echo "       default-agent"
echo "       scan on"
echo "       pair <MAC>"
echo "       trust <MAC>"
echo "       connect <MAC>"
echo "  4. Reboot. The stick should reconnect by itself."
echo
echo "[setup] Done. Reboot recommended."
echo "  sudo systemctl start chaos-arcade.service"
echo "  or windowed: CHAOS_WINDOWED=1 $ROOT/.venv/bin/python3 $ROOT/main.py"
echo "  Full walkthrough: $ROOT/RASPBERRY_PI.md"
