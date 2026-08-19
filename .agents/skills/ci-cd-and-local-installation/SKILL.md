---
name: ci-cd-and-local-installation
description: Use when building standalone binaries, compiling locally, setting up desktop integration, or releasing new versions via GitHub Actions CI/CD for IA Tools Manager (ia-tools)
---

# CI/CD, Local Compilation & Installation Guide

## Overview

This skill teaches the complete build, packaging, local desktop installation, and automated multi-platform release (CI/CD) workflows for the **IA Tools Manager** (`ia-tools`) codebase.

---

## Architecture & Build Pipeline

```
                               ┌────────────────────────┐
                               │   Local Development    │
                               │     (app.py / Qt6)     │
                               └───────────┬────────────┘
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    ▼                                             ▼
       ┌─────────────────────────┐                   ┌─────────────────────────┐
       │   Local Build Script    │                   │   GitHub Actions CI/CD  │
       │       (./build.sh)      │                   │  (.github/workflows/)   │
       └────────────┬────────────┘                   └────────────┬────────────┘
                    │                                             │
      ┌─────────────┴─────────────┐                 ┌─────────────┴─────────────┐
      ▼                           ▼                 ▼             ▼             ▼
[dist/ia-tools]          [~/.local/bin/ia-tools] [Linux ELF] [macOS Mach-O] [Windows EXE]
                         [~/.local/share/apps]      │             │             │
                                                    └─────────────┼─────────────┘
                                                                  ▼
                                                          [GitHub Release Assets]
```

---

## 1. Local Compilation & Installation

### The `build.sh` Script

Running `./build.sh` performs end-to-end environment preparation, compilation, binary output, and system launcher registration:

```bash
./build.sh
```

### Key Technical Mechanisms in `build.sh`:

#### 1. Atomic Binary Replacement (Prevents "Text file busy" / `ETXTBSY`)
When an application is currently running, overwriting its binary directly with `cp dist/ia-tools ~/.local/bin/ia-tools` causes the Linux kernel error: `cp: não foi possível criar arquivo comum ...: Área de texto ocupada`.
The solution is atomic inode replacement using a temporary file and `mv -f`:

```bash
mkdir -p "$HOME/.local/bin"
cp dist/ia-tools "$HOME/.local/bin/ia-tools.tmp"
mv -f "$HOME/.local/bin/ia-tools.tmp" "$HOME/.local/bin/ia-tools"
chmod +x "$HOME/.local/bin/ia-tools"
```

#### 2. PyInstaller Configuration
The build uses PyInstaller with dynamic data assets and hidden imports:
```bash
./.venv/bin/pyinstaller \
  --name "ia-tools" \
  --onefile \
  --windowed \
  --add-data "assets:assets" \
  --hidden-import "qtawesome.icon_browser" \
  --hidden-import "json5" \
  --clean \
  --noconfirm \
  app.py
```

#### 3. Linux Desktop Drawer & Icon Integration
The script installs the application icon and `.desktop` entry to user-level XDG directories:
- **Icon**: `~/.local/share/icons/hicolor/512x512/apps/ia-tools.png`
- **Desktop Entry**: `~/.local/share/applications/ia-tools.desktop`
- **MIME & Desktop Cache Update**: `update-desktop-database ~/.local/share/applications/` and `gtk-update-icon-cache` (if available).

---

## 2. GitHub Actions Automated Multi-Platform CI/CD

The workflow at [`.github/workflows/release.yml`](.github/workflows/release.yml) automatically triggers whenever a version tag (`v*.*.*`) is pushed.

### Matrix Build Strategy

| Platform / OS | Runner | Output Binary Name | PyInstaller Flag |
|---|---|---|---|
| 🐧 **Linux (x86_64)** | `ubuntu-24.04` | `ia-tools-linux-x86_64` | `--onefile --windowed` |
| 🍏 **macOS** | `macos-latest` | `ia-tools-macos` | `--onefile --windowed` |
| 🪟 **Windows** | `windows-latest` | `ia-tools-windows.exe` | `--onefile --windowed` |

### Triggering a New Release via Tag

To publish a new official release across all 3 operating systems:

```bash
# 1. Ensure all changes are committed and pushed on main
git status
git push origin main

# 2. Create the version tag
git tag v1.0.2

# 3. Push the tag to GitHub (Triggers CI/CD)
git push origin v1.0.2

# 4. (Optional) Create the GitHub Release directly with GitHub CLI
gh release create v1.0.2 dist/ia-tools#ia-tools-linux-x86_64 \
  --title "v1.0.2 - IA Tools Manager" \
  --notes "Summary of new features and bug fixes in this release."
```

---

## 3. Quick Reference Commands

| Action | Command |
|---|---|
| **Run in Dev Mode** | `./launcher.sh` |
| **Run Unit Tests** | `./.venv/bin/python3 -m unittest discover tests/` |
| **Recompile & Install Locally** | `./build.sh` |
| **Launch Installed Binary** | `ia-tools` |
| **Inspect Running Tasks** | `ps aux \| grep ia-tools` |
| **View GitHub Actions Status** | `gh run list` |
| **View Releases** | `gh release list` |

---

## 4. Common Troubleshooting & Gotchas

### 1. `ETXTBSY` / "Área de texto ocupada"
- **Cause**: Trying to write directly to a running executable's disk location.
- **Fix**: Never use `cp dist/ia-tools ~/.local/bin/ia-tools` directly while running. Always copy to `.tmp` and `mv -f` to swap the directory pointer.

### 2. Missing Qt Plugins / `libxcb-cursor.so`
- **Cause**: PyInstaller on minimal headless servers might not include platform XCB plugins.
- **Fix**: The spec file bundles `PyQt6` and `qtawesome` data automatically. On target machines, standard `libxcb` and `libGL` packages provide hardware rendering.

### 3. Wayland vs X11 Display
- **Default**: PyQt6 automatically detects Wayland (`WAYLAND_DISPLAY`) or X11 (`DISPLAY`).
- **Forced Mode (if needed)**: `QT_QPA_PLATFORM=xcb ia-tools` or `QT_QPA_PLATFORM=wayland ia-tools`.
