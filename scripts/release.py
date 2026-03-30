#!/usr/bin/env python3
# Run: python3 scripts/release.py <version> [--dry-run]
"""Bump version across all files, generate changelog, commit, and tag.

Usage:
    python scripts/release.py 0.2.0          # bump to 0.2.0
    python scripts/release.py 0.2.0 --dry-run  # preview without writing
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import textwrap
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INIT_FILE = ROOT / "shush" / "__init__.py"
PYPROJECT_FILE = ROOT / "pyproject.toml"
DEBIAN_CHANGELOG = ROOT / "debian" / "changelog"
CHANGELOG_FILE = ROOT / "CHANGELOG.md"

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def run(cmd: str, **kw) -> str:
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=ROOT, **kw)
    return r.stdout.strip()


def current_version() -> str:
    text = INIT_FILE.read_text()
    m = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', text)
    if not m:
        sys.exit("Cannot find __version__ in shush/__init__.py")
    return m.group(1)


def last_tag() -> str | None:
    tag = run("git describe --tags --abbrev=0 2>/dev/null")
    return tag if tag else None


def git_log_since(tag: str | None) -> list[str]:
    if tag:
        raw = run(f"git log {tag}..HEAD --pretty=format:%s")
    else:
        raw = run("git log --pretty=format:%s")
    return [l.strip() for l in raw.splitlines() if l.strip()]


def categorize(messages: list[str]) -> dict[str, list[str]]:
    cats: dict[str, list[str]] = {"Features": [], "Fixes": [], "Other": []}
    for msg in messages:
        lower = msg.lower()
        if msg.startswith("release:"):
            continue
        if lower.startswith("feat"):
            cleaned = re.sub(r"^feat\w*:\s*", "", msg, flags=re.IGNORECASE)
            cats["Features"].append(cleaned)
        elif lower.startswith("fix"):
            cleaned = re.sub(r"^fix\w*:\s*", "", msg, flags=re.IGNORECASE)
            cats["Fixes"].append(cleaned)
        else:
            cats["Other"].append(msg)
    return {k: v for k, v in cats.items() if v}


def build_changelog_section(version: str, cats: dict[str, list[str]]) -> str:
    today = date.today().isoformat()
    lines = [f"## {version} — {today}", ""]
    for category, items in cats.items():
        lines.append(f"### {category}")
        lines.append("")
        for item in items:
            lines.append(f"- {item}")
        lines.append("")
    return "\n".join(lines)


def update_init(new_ver: str, dry_run: bool) -> None:
    text = INIT_FILE.read_text()
    updated = re.sub(
        r'__version__\s*=\s*["\'][^"\']+["\']',
        f'__version__ = "{new_ver}"',
        text,
    )
    if dry_run:
        print(f"  [dry-run] shush/__init__.py: __version__ = \"{new_ver}\"")
    else:
        INIT_FILE.write_text(updated)


def update_pyproject(new_ver: str, dry_run: bool) -> None:
    text = PYPROJECT_FILE.read_text()
    updated = re.sub(
        r'^version\s*=\s*"[^"]+"',
        f'version = "{new_ver}"',
        text,
        flags=re.MULTILINE,
    )
    if dry_run:
        print(f"  [dry-run] pyproject.toml: version = \"{new_ver}\"")
    else:
        PYPROJECT_FILE.write_text(updated)


def update_debian_changelog(new_ver: str, dry_run: bool) -> None:
    today = date.today().strftime("%a, %d %b %Y %H:%M:%S +0000")
    maintainer = run("git config user.name") or "Eslam Elshiekh"
    email = run("git config user.email") or "eslam@example.com"
    entry = textwrap.dedent(f"""\
        shush ({new_ver}-1) unstable; urgency=low

          * Release {new_ver}.

         -- {maintainer} <{email}>  {today}

    """)
    if dry_run:
        print(f"  [dry-run] debian/changelog: prepend {new_ver}-1 entry")
    else:
        existing = DEBIAN_CHANGELOG.read_text()
        DEBIAN_CHANGELOG.write_text(entry + existing)


def update_changelog_md(section: str, dry_run: bool) -> None:
    if dry_run:
        print(f"  [dry-run] CHANGELOG.md: prepend new section")
        print(textwrap.indent(section, "    "))
        return
    text = CHANGELOG_FILE.read_text()
    marker = "# Changelog"
    if marker in text:
        text = text.replace(marker, f"{marker}\n\n{section}", 1)
    else:
        text = f"{marker}\n\n{section}\n{text}"
    CHANGELOG_FILE.write_text(text)


def git_commit_and_tag(new_ver: str, dry_run: bool) -> None:
    if dry_run:
        print(f"  [dry-run] git commit -m \"release: v{new_ver}\"")
        print(f"  [dry-run] git tag v{new_ver}")
        return
    run("git add -A")
    run(f'git commit -m "release: v{new_ver}"')
    run(f"git tag v{new_ver}")
    print(f"  Created commit and tag v{new_ver}")
    print(f"  Push with: git push && git push --tags")


def main():
    parser = argparse.ArgumentParser(description="Bump Shush version and create release tag")
    parser.add_argument("version", help="New version (e.g. 0.2.0)")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    args = parser.parse_args()

    new_ver = args.version
    if not SEMVER_RE.match(new_ver):
        sys.exit(f"Invalid semver: {new_ver} (expected X.Y.Z)")

    old_ver = current_version()
    if new_ver == old_ver:
        sys.exit(f"Version {new_ver} is already the current version")

    tag = last_tag()
    messages = git_log_since(tag)
    cats = categorize(messages)

    if not cats:
        cats = {"Other": [f"Release {new_ver}"]}

    section = build_changelog_section(new_ver, cats)

    print(f"Bumping {old_ver} -> {new_ver}" + (" (dry run)" if args.dry_run else ""))
    print()

    update_init(new_ver, args.dry_run)
    update_pyproject(new_ver, args.dry_run)
    update_debian_changelog(new_ver, args.dry_run)
    update_changelog_md(section, args.dry_run)

    if not args.dry_run:
        print("  Updated shush/__init__.py")
        print("  Updated pyproject.toml")
        print("  Updated debian/changelog")
        print("  Updated CHANGELOG.md")

    print()
    git_commit_and_tag(new_ver, args.dry_run)


if __name__ == "__main__":
    main()
