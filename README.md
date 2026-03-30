# Shush

**Linux notification filter with a GUI rule editor.**

Shush sits on the D-Bus session bus, watches every desktop notification, and
instantly suppresses the ones you don't care about. Only the notifications
matching your keyword rules make it through — your boss's messages, Teams
calls, urgent alerts — everything else is silenced.

Works on **any Linux desktop environment** (GNOME, KDE, XFCE, Sway, i3, …)
without replacing your notification daemon.

---

## Why Shush?

| Feature | Shush | GNOME NotifyFilter | Dunst rules | nofi |
|---|---|---|---|---|
| Works on any DE | Yes | GNOME 45+ only | Yes (replaces daemon) | Yes (replaces daemon) |
| GUI rule editor | Yes | Basic | No (config file) | No |
| Per-person rules | Yes | No | Manual | No |
| Per-app filtering | Yes | No | Yes | Partial |
| Keywords + regex | Yes | Text only | Regex | No |
| Live activity log | Yes | No | No | No |
| Focus-mode presets | Yes | No | No | No |
| System tray | Yes | N/A | N/A | N/A |
| pip installable | Yes | No | No | cargo |
| No daemon replacement | Yes | Yes | No | No |

---

## Installation

### From PyPI (recommended)

```bash
pip install shush-notifications
```

### From source

```bash
git clone https://github.com/eslamsalahelsheikh/shush.git
cd shush
pip install .
```

### Debian / Ubuntu (.deb)

```bash
sudo apt install python3-pyqt5 python3-dbus python3-gi
dpkg-buildpackage -us -uc
sudo dpkg -i ../shush_0.1.0-1_all.deb
```

### System dependencies

Shush needs these system packages (most distros have them pre-installed):

- Python 3.8+
- PyQt5
- dbus-python
- PyGObject (GLib introspection)

On Ubuntu/Debian:

```bash
sudo apt install python3-pyqt5 python3-dbus python3-gi gir1.2-glib-2.0
```

On Fedora:

```bash
sudo dnf install python3-qt5 python3-dbus python3-gobject
```

On Arch:

```bash
sudo pacman -S python-pyqt5 python-dbus python-gobject
```

---

## Usage

```bash
# Launch with GUI
shush

# Start minimized to system tray
shush --minimized

# Dry run — log what would be suppressed without actually closing anything
shush --dry-run

# Verbose logging
shush -v
```

### Auto-start on login

Copy the systemd user service:

```bash
mkdir -p ~/.config/systemd/user
cp data/shush.service ~/.config/systemd/user/
systemctl --user enable --now shush.service
```

Or copy the `.desktop` file:

```bash
cp data/shush.desktop ~/.config/autostart/
```

---

## How It Works

```
┌──────────────────────────────────────────────┐
│  Your Apps (Slack, Teams, Firefox, …)        │
│  send Notify() over D-Bus                    │
└──────────┬───────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────┐
│  Notification Daemon                         │
│  (gnome-shell / KDE / dunst / mako / …)     │
│  displays the notification, returns an ID    │
└──────────┬───────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────┐
│  Shush (message filter on the session bus)   │
│                                              │
│  1. Intercepts the Notify() arguments        │
│  2. Checks keywords against your rules       │
│  3. If no rule matches → CloseNotification() │
│  4. If a rule matches → notification stays   │
└──────────────────────────────────────────────┘
```

Shush **does not replace** your notification daemon. It eavesdrops on the
D-Bus session bus and calls `CloseNotification(id)` on notifications that
don't match your rules. This means it works alongside whatever notification
system your desktop already uses.

---

## Configuration

Rules are stored in `~/.config/shush/rules.json`. You can edit them through
the GUI or by hand. Send `SIGHUP` to reload after manual edits:

```bash
kill -HUP $(pgrep -f 'python.*shush')
```

### Rule structure

Each rule has:

- **Name** — a human label (e.g., "Boss — Ahmed")
- **Action** — `allow` or `block`
- **Keywords** — list of strings (or regex patterns) to match
- **Match fields** — which notification fields to search: `app_name`, `summary`, `body`
- **App filter** — optional, restrict the rule to a specific app (e.g., "Slack")
- **Use regex** — treat keywords as regular expressions
- **Enabled** — toggle without deleting

### Modes

- **Whitelist (default):** suppress everything; only notifications matching
  an "allow" rule get through.
- **Blacklist:** allow everything; only notifications matching a "block" rule
  are suppressed.

### Focus presets

Create named presets (e.g., "Meeting", "Deep Work") that activate only a
subset of your rules. Switch presets from the Settings tab or the system tray.

---

## Contributing

Contributions are welcome! Please open an issue first to discuss what you'd
like to change.

```bash
git clone https://github.com/eslamsalahelsheikh/shush.git
cd shush
pip install -e .
shush --verbose
```

---

## License

[Apache License 2.0](LICENSE)
