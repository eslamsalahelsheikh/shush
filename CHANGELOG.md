# Changelog

## 0.2.0 — 2026-03-30

### Features

- add versioning and release system
- add About page with app info, links, and credits
- modern dark theme UI with Catppuccin Mocha styling
- add notification sound control
- single-instance lock via abstract Unix socket

### Fixes

- replace emojis with plain Unicode symbols for Qt compatibility
- update About nav icon and change author to Eslam Elshiekh
- left-align sidebar nav items with consistent padding
- settings tab resizes properly with scrollable layout
- repair duplicate rules, settings layout, and close dialog
- generate unique IDs for new rules
- enable D-Bus eavesdrop and deduplicate filter callbacks

### Other

- Initial release of Shush v0.1.0


## 0.1.0 — 2026-03-30

Initial release.

- D-Bus notification monitoring and suppression via `CloseNotification`.
- PyQt5 GUI with three tabs: Rules, Activity Log, Settings.
- Per-person and per-app keyword rules with drag-and-drop priority ordering.
- Support for plain keywords and regular expressions.
- Focus-mode presets — activate a named subset of rules with one click.
- System tray integration with pause/resume.
- Whitelist mode (suppress all, allow matching) and blacklist mode (allow all, block matching).
- Live colour-coded activity log with CSV export.
- Hot-reload via SIGHUP.
- `--dry-run` and `--verbose` CLI flags.
- `pip install` and `.deb` packaging.
