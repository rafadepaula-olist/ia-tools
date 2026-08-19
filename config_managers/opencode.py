import os
import shutil
from typing import List, Dict, Any, Optional
from models.mcp import McpServer
from models.plugin import PluginSkill
from .base import BaseConfigManager

class OpenCodeConfigManager(BaseConfigManager):
    AGENT_NAME = "OpenCode"

    def __init__(self):
        home = os.path.expanduser("~")
        self.config_dir = os.path.join(home, ".config", "opencode")
        self.jsonc_file = os.path.join(self.config_dir, "opencode.jsonc")
        self.json_file = os.path.join(self.config_dir, "opencode.json")
        self.plugins_dir = os.path.join(self.config_dir, "plugins")
        self.skills_dir = os.path.join(self.config_dir, "skills")

    def _get_active_config_path(self) -> str:
        if os.path.exists(self.jsonc_file):
            return self.jsonc_file
        if os.path.exists(self.json_file):
            return self.json_file
        return self.jsonc_file

    def _get_shelved_path(self) -> str:
        return self.get_shelved_filepath(self._get_active_config_path())

    def list_mcps(self) -> List[McpServer]:
        servers: List[McpServer] = []
        seen = set()
        cfg_path = self._get_active_config_path()
        data = self.read_json_file(cfg_path)
        mcp_dict = data.get("mcp", {})

        for name, cfg in mcp_dict.items():
            if not isinstance(cfg, dict):
                continue
            
            server_type = cfg.get("type", "local")
            enabled = cfg.get("enabled", True)
            url = cfg.get("url", "")
            headers = cfg.get("headers", {})
            env = cfg.get("environment", {})
            
            cmd_raw = cfg.get("command", [])
            command = ""
            args = []
            if isinstance(cmd_raw, list) and len(cmd_raw) > 0:
                command = cmd_raw[0]
                args = cmd_raw[1:]
            elif isinstance(cmd_raw, str):
                command = cmd_raw

            seen.add(name)
            servers.append(McpServer(
                name=name,
                server_type=server_type,
                command=command if command else None,
                args=args,
                env=env if isinstance(env, dict) else {},
                url=url if url else None,
                headers=headers if isinstance(headers, dict) else {},
                enabled=bool(enabled),
                raw_data=cfg,
                source_file=cfg_path
            ))

        # Shelved MCPs
        for sm in self.read_shelved_mcps(self._get_shelved_path()):
            if sm.name not in seen:
                seen.add(sm.name)
                servers.append(sm)

        return sorted(servers, key=lambda x: x.name.lower())

    def save_mcp(self, mcp: McpServer) -> bool:
        if getattr(mcp, 'shelved', False):
            self.delete_mcp(mcp.name)
            return self.write_shelved_mcp(self._get_shelved_path(), mcp)

        self.delete_shelved_mcp(self._get_shelved_path(), mcp.name)

        cfg_path = self._get_active_config_path()
        data = self.read_json_file(cfg_path)
        if "mcp" not in data:
            data["mcp"] = {}

        data["mcp"][mcp.name] = mcp.to_opencode_dict()
        return self.write_json_file(cfg_path, data)

    def shelve_mcp(self, mcp: McpServer) -> bool:
        """Temporarily removes MCP from OpenCode config and stores in sidecar shelved file."""
        self.delete_mcp(mcp.name)
        return self.write_shelved_mcp(self._get_shelved_path(), mcp)

    def unshelve_mcp(self, mcp: McpServer) -> bool:
        """Restores a shelved MCP back into the active OpenCode config."""
        restored = self.remove_shelved_mcp(self._get_shelved_path(), mcp.name)
        if restored:
            restored.shelved = False
            restored.enabled = True
            return self.save_mcp(restored)
        mcp.shelved = False
        mcp.enabled = True
        return self.save_mcp(mcp)

    def toggle_mcp(self, name: str, enable: bool) -> bool:
        mcps = self.list_mcps()
        target = next((m for m in mcps if m.name == name), None)
        if not target:
            return False
        target.enabled = enable
        return self.save_mcp(target)

    def delete_mcp(self, name: str) -> bool:
        self.delete_shelved_mcp(self._get_shelved_path(), name)
        cfg_path = self._get_active_config_path()
        data = self.read_json_file(cfg_path)
        if "mcp" in data and name in data["mcp"]:
            del data["mcp"][name]
            return self.write_json_file(cfg_path, data)
        return False

    def list_plugins_and_skills(self, project_path: Optional[str] = None) -> List[PluginSkill]:
        items: List[PluginSkill] = []
        cfg_path = self._get_active_config_path()
        data = self.read_json_file(cfg_path)

        active_plugins = data.get("plugin", [])
        disabled_plugins = data.get("_disabledPlugin", [])

        # 1. Registered plugins
        for p in active_plugins:
            name = os.path.basename(p) if "/" in p else p
            items.append(PluginSkill(
                name=name,
                kind="plugin",
                enabled=True,
                source=p,
                path=p if os.path.isabs(p) else os.path.join(self.config_dir, p),
                description=f"OpenCode Plugin ({p})",
                source_file=cfg_path,
                metadata={"raw": p}
            ))

        for p in disabled_plugins:
            name = os.path.basename(p) if "/" in p else p
            items.append(PluginSkill(
                name=name,
                kind="plugin",
                enabled=False,
                source=p,
                path=p if os.path.isabs(p) else os.path.join(self.config_dir, p),
                description=f"OpenCode Plugin ({p}) [Disabled]",
                source_file=cfg_path,
                metadata={"raw": p}
            ))

        # 2. Plugins in ~/.config/opencode/plugins/
        if os.path.exists(self.plugins_dir):
            for entry in os.listdir(self.plugins_dir):
                entry_path = os.path.join(self.plugins_dir, entry)
                if os.path.isdir(entry_path) and not entry.startswith('.'):
                    # Check if already listed
                    if not any(it.name == entry for it in items):
                        items.append(PluginSkill(
                            name=entry,
                            kind="plugin",
                            enabled=any(entry in str(p) for p in active_plugins),
                            source=f"~/.config/opencode/plugins/{entry}",
                            path=entry_path,
                            description=f"Local Plugin Directory ({entry})",
                            source_file=cfg_path,
                            metadata={"raw": f"./plugins/{entry}"}
                        ))

        # 3. Skills in ~/.config/opencode/skills/
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
                        source="~/.config/opencode/skills",
                        path=entry_path,
                        description=desc or f"Skill {entry}",
                        source_file=self.skills_dir
                    ))

        # 4. Project-specific skills
        if project_path:
            items.extend(self.scan_project_skills(project_path))
        else:
            for p in self.get_known_projects():
                items.extend(self.scan_project_skills(p))

        return sorted(items, key=lambda x: (x.kind, x.name.lower()))

    def toggle_plugin_skill(self, item: PluginSkill, enable: bool) -> bool:
        cfg_path = self._get_active_config_path()
        data = self.read_json_file(cfg_path)

        if item.kind == "plugin":
            raw_plugin = item.metadata.get("raw", item.source)
            active_list = data.get("plugin", [])
            disabled_list = data.get("_disabledPlugin", [])

            if enable:
                # Move to active
                if raw_plugin in disabled_list:
                    disabled_list.remove(raw_plugin)
                if raw_plugin not in active_list:
                    active_list.append(raw_plugin)
            else:
                # Move to disabled
                if raw_plugin in active_list:
                    active_list.remove(raw_plugin)
                if raw_plugin not in disabled_list:
                    disabled_list.append(raw_plugin)

            data["plugin"] = active_list
            data["_disabledPlugin"] = disabled_list
            return self.write_json_file(cfg_path, data)
        else: # skill
            if item.path and os.path.exists(item.path):
                parent = os.path.dirname(item.path)
                base = os.path.basename(item.path)
                if enable and base.endswith('.disabled'):
                    new_name = base[:-9]
                    new_path = os.path.join(parent, new_name)
                    os.rename(item.path, new_path)
                    item.path = new_path
                    item.name = new_name
                    item.enabled = True
                    return True
                elif not enable and not base.endswith('.disabled'):
                    new_name = f"{base}.disabled"
                    new_path = os.path.join(parent, new_name)
                    os.rename(item.path, new_path)
                    item.path = new_path
                    item.name = new_name
                    item.enabled = False
                    return True
            return True

    def add_plugin(self, plugin_entry: str) -> bool:
        cfg_path = self._get_active_config_path()
        data = self.read_json_file(cfg_path)
        if "plugin" not in data:
            data["plugin"] = []
        if plugin_entry not in data["plugin"]:
            data["plugin"].append(plugin_entry)
        return self.write_json_file(cfg_path, data)

    def add_skill(self, name: str, description: str, instructions: str) -> bool:
        target_dir = self.skills_dir
        os.makedirs(target_dir, exist_ok=True)
        self.create_skill_folder(target_dir, name, description, instructions)
        return True

    def delete_plugin_skill(self, item: PluginSkill) -> bool:
        cfg_path = self._get_active_config_path()
        data = self.read_json_file(cfg_path)
        raw_plugin = item.metadata.get("raw", item.source)

        if item.kind == "plugin":
            modified = False
            if "plugin" in data and raw_plugin in data["plugin"]:
                data["plugin"].remove(raw_plugin)
                modified = True
            if "_disabledPlugin" in data and raw_plugin in data["_disabledPlugin"]:
                data["_disabledPlugin"].remove(raw_plugin)
                modified = True
            if modified:
                self.write_json_file(cfg_path, data)
        elif item.kind == "skill":
            if item.path and os.path.exists(item.path):
                # Don't follow symlinks — remove the link itself, not its target
                if os.path.islink(item.path):
                    os.unlink(item.path)
                    return True
                backup_dest = os.path.join(self.BACKUP_DIR, f"deleted_{os.path.basename(item.path)}")
                try:
                    if os.path.exists(backup_dest):
                        shutil.rmtree(backup_dest, ignore_errors=True)
                    shutil.move(item.path, backup_dest)
                    return True
                except Exception as e:
                    print(f"Error removing skill folder: {e}")
                    return False
        return True

    def get_raw_config_path(self) -> str:
        return self._get_active_config_path()

    def get_raw_config(self) -> Dict[str, Any]:
        return self.read_json_file(self._get_active_config_path())

    def save_raw_config(self, data: Dict[str, Any]) -> bool:
        return self.write_json_file(self._get_active_config_path(), data)

    def is_installed(self) -> bool:
        """Detects if OpenCode is installed or present on the system."""
        # 1. Config directory and files
        if os.path.exists(self.config_dir) and os.path.isdir(self.config_dir):
            return True
        if os.path.exists(self.jsonc_file) or os.path.exists(self.json_file):
            return True
        home = os.path.expanduser("~")
        if os.path.exists(os.path.join(home, ".opencode")):
            return True
        if os.path.exists(self.plugins_dir) or os.path.exists(self.skills_dir):
            return True

        # 2. Executables in PATH
        if shutil.which("opencode"):
            return True

        return False

