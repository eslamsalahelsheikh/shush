# Changelog

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
