---
name: extending-ia-tools-providers
description: Use when adding support for a new AI agent or provider (such as Codex, Windsurf, Cursor, Goose, Copilot) to IA Tools Manager (ia-tools)
---

# Extending IA Tools Providers

## Overview

This skill provides the architectural pattern and step-by-step instructions for adding new AI agent providers (e.g., **Codex**, **Windsurf**, **Cursor**, **Goose**, **Zed**) to the **IA Tools Manager** (`ia-tools`) desktop application.

Adding a provider requires 4 coordinated steps:
1. Model conversion methods in `models/mcp.py`
2. Config manager subclass in `config_managers/<provider>.py` (implementing `is_installed()`, `list_mcps()`, `save_mcp()`, etc.)
3. UI registration in `PROVIDER_REGISTRY` in `ui/main_window.py` and `ui/agent_tab.py`
4. Automated unit test in `tests/test_managers.py`

```
┌─────────────────────────────────────────────────────────────┐
│                       IA-TOOLS HARNESS                      │
│                                                             │
│   ┌───────────────┐     ┌───────────────────────────────┐   │
│   │ Models Layer  │ ──► │ Config Manager (BaseClass)    │   │
│   │ (McpServer)   │     │ (read_json, write_json,       │   │
│   │               │     │  is_installed detection)      │   │
│   └───────────────┘     └──────────────┬────────────────┘   │
│                                        │                    │
│                                        ▼                    │
│                         ┌───────────────────────────────┐   │
│                         │ Dynamic UI Layer              │   │
│                         │ (PROVIDER_REGISTRY Discovery  │   │
│                         │  + AgentTab & Cards)          │   │
│                         └───────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Known Agent Config Paths Reference

| Agent / Provider | Config File Path | MCP Section Key | Skills / Plugins Path | Detection Trigger |
|---|---|---|---|---|
| **Codex** | `~/.codex/config.json` or `~/.agents/config.json` | `mcpServers` | `~/.agents/skills/` | `~/.codex` or `codex` CLI |
| **Windsurf** | `~/.codeium/windsurf/mcp_config.json` | `mcpServers` | `~/.codeium/windsurf/skills/` | `~/.codeium/windsurf` or `windsurf` CLI |
| **Cursor** | `~/.cursor/mcp.json` or `~/.config/Cursor/User/globalStorage/...` | `mcpServers` | `~/.cursor/extensions/` | `~/.cursor` or `cursor` CLI |
| **Goose** | `~/.config/goose/config.yaml` or `~/.goose/mcp.json` | `extensions` / `mcp` | `~/.goose/recipes/` | `~/.config/goose` or `goose` CLI |
| **Zed** | `~/.config/zed/settings.json` | `context_servers` | `~/.config/zed/extensions/` | `~/.config/zed` or `zed` CLI |

---

## Step-by-Step Implementation Guide

### Step 1: Add Format Conversion to `models/mcp.py`

Define how an `McpServer` converts into the provider's specific JSON schema.

```python
# models/mcp.py

def to_windsurf_dict(self) -> Dict[str, Any]:
    """Convert to Windsurf / Codeium MCP format."""
    if self.is_remote:
        return {
            "serverUrl": self.url,
            "headers": self.headers
        }
    else:
        d = {"command": self.command or "npx"}
        if self.args:
            d["args"] = self.args
        if self.env:
            d["env"] = self.env
        return d
```

---

### Step 2: Implement `config_managers/<provider>.py`

Create a new manager inheriting from `BaseConfigManager`. Make sure to implement `is_installed()` so IA Tools Manager can automatically discover whether this tool is installed on the user's computer.

```python
# config_managers/windsurf.py
import os
import shutil
from typing import List, Dict, Any, Optional
from models.mcp import McpServer
from models.plugin import PluginSkill
from .base import BaseConfigManager

class WindsurfConfigManager(BaseConfigManager):
    def __init__(self):
        home = os.path.expanduser("~")
        self.config_dir = os.path.join(home, ".codeium", "windsurf")
        self.mcp_file = os.path.join(self.config_dir, "mcp_config.json")
        self.skills_dir = os.path.join(self.config_dir, "skills")

    def is_installed(self) -> bool:
        """Determines if Windsurf is installed or present on the system."""
        if os.path.exists(self.config_dir) and os.path.isdir(self.config_dir):
            return True
        if os.path.exists(self.mcp_file):
            return True
        if shutil.which("windsurf"):
            return True
        return False

    def list_mcps(self) -> List[McpServer]:
        servers: List[McpServer] = []
        data = self.read_json_file(self.mcp_file)
        
        # Active servers
        active_dict = data.get("mcpServers", {})
        for name, cfg in active_dict.items():
            if isinstance(cfg, dict):
                servers.append(self._dict_to_mcp(name, cfg, enabled=True))

        # Disabled servers (stored in _disabledMcpServers)
        disabled_dict = data.get("_disabledMcpServers", {})
        for name, cfg in disabled_dict.items():
            if isinstance(cfg, dict):
                servers.append(self._dict_to_mcp(name, cfg, enabled=False))

        return sorted(servers, key=lambda x: x.name.lower())

    def _dict_to_mcp(self, name: str, cfg: Dict[str, Any], enabled: bool) -> McpServer:
        url = cfg.get("serverUrl") or cfg.get("url", "")
        return McpServer(
            name=name,
            server_type="http" if url else "stdio",
            command=cfg.get("command"),
            args=cfg.get("args", []),
            env=cfg.get("env", {}),
            url=url if url else None,
            headers=cfg.get("headers", {}),
            enabled=enabled,
            raw_data=cfg,
            source_file=self.mcp_file
        )

    def save_mcp(self, mcp: McpServer) -> bool:
        data = self.read_json_file(self.mcp_file)
        if "mcpServers" not in data:
            data["mcpServers"] = {}
        if "_disabledMcpServers" not in data:
            data["_disabledMcpServers"] = {}

        data["mcpServers"].pop(mcp.name, None)
        data["_disabledMcpServers"].pop(mcp.name, None)

        mcp_dict = mcp.to_windsurf_dict() if hasattr(mcp, 'to_windsurf_dict') else mcp.to_claude_dict()

        if mcp.enabled:
            data["mcpServers"][mcp.name] = mcp_dict
        else:
            data["_disabledMcpServers"][mcp.name] = mcp_dict

        return self.write_json_file(self.mcp_file, data)

    def toggle_mcp(self, name: str, enable: bool) -> bool:
        mcps = self.list_mcps()
        target = next((m for m in mcps if m.name == name), None)
        if not target:
            return False
        target.enabled = enable
        return self.save_mcp(target)

    def delete_mcp(self, name: str) -> bool:
        data = self.read_json_file(self.mcp_file)
        modified = False
        if "mcpServers" in data and name in data["mcpServers"]:
            del data["mcpServers"][name]
            modified = True
        if "_disabledMcpServers" in data and name in data["_disabledMcpServers"]:
            del data["_disabledMcpServers"][name]
            modified = True

        return self.write_json_file(self.mcp_file, data) if modified else False

    def list_plugins_and_skills(self) -> List[PluginSkill]:
        items: List[PluginSkill] = []
        if os.path.exists(self.skills_dir):
            for entry in os.listdir(self.skills_dir):
                entry_path = os.path.join(self.skills_dir, entry)
                if os.path.isdir(entry_path) and not entry.startswith('.'):
                    skill_md = os.path.join(entry_path, "SKILL.md")
                    title, desc = self.parse_skill_md(skill_md)
                    is_enabled = not entry.endswith('.disabled')
                    items.append(PluginSkill(
                        name=entry,
                        kind="skill",
                        enabled=is_enabled,
                        source="~/.codeium/windsurf/skills",
                        path=entry_path,
                        description=desc or f"Skill {entry}",
                        source_file=self.skills_dir
                    ))
        return sorted(items, key=lambda x: x.name.lower())

    def toggle_plugin_skill(self, item: PluginSkill, enable: bool) -> bool:
        if item.path and os.path.exists(item.path):
            parent = os.path.dirname(item.path)
            base = os.path.basename(item.path)
            if enable and base.endswith('.disabled'):
                new_path = os.path.join(parent, base[:-9])
                os.rename(item.path, new_path)
                return True
            elif not enable and not base.endswith('.disabled'):
                new_path = os.path.join(parent, f"{base}.disabled")
                os.rename(item.path, new_path)
                return True
        return True

    def add_skill(self, name: str, description: str, instructions: str) -> bool:
        os.makedirs(self.skills_dir, exist_ok=True)
        self.create_skill_folder(self.skills_dir, name, description, instructions)
        return True

    def delete_plugin_skill(self, item: PluginSkill) -> bool:
        if item.path and os.path.exists(item.path):
            backup_dest = os.path.join(self.BACKUP_DIR, f"deleted_{os.path.basename(item.path)}")
            shutil.move(item.path, backup_dest)
            return True
        return False

    def get_raw_config_path(self) -> str:
        return self.mcp_file

    def get_raw_config(self) -> Dict[str, Any]:
        return self.read_json_file(self.mcp_file)

    def save_raw_config(self, data: Dict[str, Any]) -> bool:
        return self.write_json_file(self.mcp_file, data)
```

Export the manager in `config_managers/__init__.py`:

```python
# config_managers/__init__.py
from .windsurf import WindsurfConfigManager

__all__ = [
    ...,
    'WindsurfConfigManager'
]
```

---

### Step 3: Register in Dynamic Discovery Registry (`ui/main_window.py` & `ui/agent_tab.py`)

1. In `ui/main_window.py`, register the provider in `PROVIDER_REGISTRY`:
```python
PROVIDER_REGISTRY = [
    ...,
    {
        "name": "Windsurf",
        "manager_cls": WindsurfConfigManager,
        "icon": "fa5s.wind",
        "color": "#10b981",
        "label": "🌊 Windsurf",
        "desc": "Codeium Windsurf IDE (~/.codeium/windsurf)"
    }
]
```
> **Note**: Because tabs are discovered dynamically, `MainWindow.discover_agents()` will call `WindsurfConfigManager.is_installed()` and display the Windsurf tab automatically only when installed on the user's machine!

2. In `ui/agent_tab.py` (Icon Banner Map):
```python
icon_map = {
    "Antigravity": ('fa5s.rocket', '#6366f1'),
    "Claude": ('fa5s.brain', '#c084fc'),
    "OpenCode": ('fa5s.bolt', '#38bdf8'),
    "Windsurf": ('fa5s.wind', '#10b981'),
    "Codex": ('fa5s.code', '#f59e0b')
}
```

---

### Step 4: Add Unit Tests & Rebuild

1. In `tests/test_managers.py`, add test cases for listing and detection:
```python
def test_windsurf_manager(self):
    mgr = WindsurfConfigManager()
    self.assertIsInstance(mgr.is_installed(), bool)
    mcps = mgr.list_mcps()
    self.assertIsInstance(mcps, list)
```

2. Run test and rebuild:
```bash
./.venv/bin/python3 -m unittest discover tests/
./build.sh
```

---

## Safety & Best Practices Checklist

- [ ] **Inherit from `BaseConfigManager`**: Ensures automatic timestamped backups before writing to any file.
- [ ] **Tolerate JSON with Comments (JSONC)**: `BaseConfigManager.read_json_file()` uses `json5` automatically.
- [ ] **Atomic Writes**: `BaseConfigManager.write_json_file()` uses temp files and atomic rename to prevent file corruption.
- [ ] **Preserve Disabled Items**: Store disabled items in `_disabledMcpServers` so toggling does not lose credentials or arguments.
