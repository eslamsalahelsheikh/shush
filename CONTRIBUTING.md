# Contributing to Shush

Thanks for your interest in improving Shush! Here's everything you need to
get started.

## Development Setup

```bash
git clone https://github.com/eslamsalahelsheikh/shush.git
cd shush
pip install -e .
```

### System dependencies

```bash
# Ubuntu / Debian
sudo apt install python3-pyqt5 python3-dbus python3-gi gir1.2-glib-2.0

# Fedora
sudo dnf install python3-qt5 python3-dbus python3-gobject

# Arch
sudo pacman -S python-pyqt5 python-dbus python-gobject
```

### Running locally

```bash
# With verbose logging (and without forking to background)
shush --verbose --no-fork

# Dry-run mode — no notifications are actually suppressed
shush --dry-run -v
```

## Running Tests

```bash
python3 -m pytest tests/ -v
```

All tests must pass before submitting a PR.

## Commit Messages

We follow the [Conventional Commits](https://www.conventionalcommits.org/)
convention:

| Prefix | When to use |
|---|---|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `test:` | Adding or updating tests |
| `docs:` | Documentation only |
| `refactor:` | Code change that neither fixes a bug nor adds a feature |
| `style:` | Formatting, missing semicolons, etc. |
| `chore:` | Build process, CI, tooling changes |

Examples:

```
feat: add time-based scheduling for rules
fix: guard config.save() against disk write errors
test: add comprehensive scheduler tests
docs: overhaul README with badges and screenshots
```

## Creating a Release

Shush uses `scripts/release.py` for version bumping and changelog generation:

```bash
python3 scripts/release.py patch   # 0.2.0 → 0.2.1
python3 scripts/release.py minor   # 0.2.0 → 0.3.0
python3 scripts/release.py major   # 0.2.0 → 1.0.0
```

This will:

1. Bump the version in `shush/__init__.py` and `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create a git tag
4. Push to trigger CI (which builds and publishes to PyPI and GitHub Releases)

## Project Structure

```
shush/
├── shush/
│   ├── __init__.py          # Version and app metadata
│   ├── app.py               # Application entry point
│   ├── config.py            # Config persistence (JSON)
│   ├── dbus_filter.py       # D-Bus notification interception
│   ├── models.py            # Data models (Rule, Schedule, etc.)
│   ├── rule_engine.py       # Rule evaluation logic
│   ├── scheduler.py         # Time-based schedule evaluation
│   └── ui/
│       ├── main_window.py   # Main window with tab navigation
│       ├── rules_tab.py     # Rule management
│       ├── log_tab.py       # Activity log with search & stats
│       ├── schedule_tab.py  # Schedule management
│       ├── settings_tab.py  # Settings panel
│       ├── rule_dialog.py   # Rule create/edit dialog
│       ├── schedule_dialog.py # Schedule create/edit dialog
│       ├── about_tab.py     # About page
│       ├── tray.py          # System tray icon & menu
│       ├── resources.py     # Theme, palette, icons
│       └── toggle_switch.py # Custom toggle switch widget
├── tests/
│   ├── test_rule_engine.py
│   └── test_scheduler.py
├── data/
│   ├── shush.desktop
│   └── shush.service
├── scripts/
│   └── release.py
├── docs/
│   └── screenshots/         # Place screenshots here
├── pyproject.toml
├── LICENSE
├── README.md
└── CONTRIBUTING.md
```

## Code Style

- Python 3.8+ compatible
- No trailing whitespace or unused imports
- Docstrings for public functions and classes
- Type hints where practical

## Submitting Changes

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/my-feature`)
3. Make your changes with clear commit messages
4. Ensure tests pass (`python3 -m pytest tests/ -v`)
5. Open a pull request against `main`

Please open an issue first for large changes to discuss the approach.
