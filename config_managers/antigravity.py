import os
import shutil
from typing import List, Dict, Any, Optional
from models.mcp import McpServer
from models.plugin import PluginSkill
from .base import BaseConfigManager

class AntigravityConfigManager(BaseConfigManager):
    def __init__(self, base_dir: Optional[str] = None):
        home = os.path.expanduser("~")
        self.gemini_dir = os.path.join(home, ".gemini")
        self.settings_file = os.path.join(self.gemini_dir, "settings.json")
        self.mcp_servers_file = os.path.join(self.gemini_dir, "mcp_servers.json")
        self.extensions_file = os.path.join(self.gemini_dir, "extensions", "extension-enablement.json")
        self.extensions_dir = os.path.join(self.gemini_dir, "extensions")
        self.skills_dir = os.path.join(self.gemini_dir, "skills")
        self.config_skills_dir = os.path.join(self.gemini_dir, "config", "skills")
        self.skills_state_file = os.path.join(self.gemini_dir, "skills_state.json")

    def list_mcps(self) -> List[McpServer]:
        servers: List[McpServer] = []
        seen = set()

        settings_data = self.read_json_file(self.settings_file)
        mcp_servers_data = self.read_json_file(self.mcp_servers_file)

        # Active MCPs in settings.json
        active_dict = settings_data.get("mcpServers", {})
        if not active_dict and "mcpServers" in mcp_servers_data:
            active_dict = mcp_servers_data.get("mcpServers", {})

        for name, cfg in active_dict.items():
            if not isinstance(cfg, dict):
                continue
            seen.add(name)
            servers.append(self._dict_to_mcp(name, cfg, enabled=True, source_file=self.settings_file))

        # Disabled MCPs (stored in _disabledMcpServers or disabledMcpServers)
        disabled_dict = settings_data.get("_disabledMcpServers", {})
        if not disabled_dict:
            disabled_dict = settings_data.get("disabledMcpServers", {})

        for name, cfg in disabled_dict.items():
            if name in seen or not isinstance(cfg, dict):
                continue
            seen.add(name)
            servers.append(self._dict_to_mcp(name, cfg, enabled=False, source_file=self.settings_file))

        return sorted(servers, key=lambda x: x.name.lower())

    def _dict_to_mcp(self, name: str, cfg: Dict[str, Any], enabled: bool, source_file: str) -> McpServer:
        server_type = cfg.get("type", "")
        url = cfg.get("url", "")
        headers = cfg.get("headers", {})
        command = cfg.get("command", "")
        args = cfg.get("args", [])
        env = cfg.get("env", {})

        if not server_type:
            if url:
                server_type = "http"
            else:
                server_type = "stdio"

        if isinstance(args, str):
            args = [args]

        return McpServer(
            name=name,
            server_type=server_type,
            command=command if command else None,
            args=args if isinstance(args, list) else [],
            env=env if isinstance(env, dict) else {},
            url=url if url else None,
            headers=headers if isinstance(headers, dict) else {},
            enabled=enabled,
            raw_data=cfg,
            source_file=source_file
        )

    def save_mcp(self, mcp: McpServer) -> bool:
        settings_data = self.read_json_file(self.settings_file)
        if "mcpServers" not in settings_data:
            settings_data["mcpServers"] = {}
        if "_disabledMcpServers" not in settings_data:
            settings_data["_disabledMcpServers"] = {}

        # Remove from both dictionaries first
        settings_data["mcpServers"].pop(mcp.name, None)
        settings_data["_disabledMcpServers"].pop(mcp.name, None)

        mcp_dict = mcp.to_antigravity_dict()

        if mcp.enabled:
            settings_data["mcpServers"][mcp.name] = mcp_dict
        else:
            settings_data["_disabledMcpServers"][mcp.name] = mcp_dict

        # Save settings.json
        res = self.write_json_file(self.settings_file, settings_data)

        # Also sync mcp_servers.json
        mcp_servers_data = self.read_json_file(self.mcp_servers_file)
        mcp_servers_data["mcpServers"] = settings_data["mcpServers"]
        if settings_data["_disabledMcpServers"]:
            mcp_servers_data["_disabledMcpServers"] = settings_data["_disabledMcpServers"]
        self.write_json_file(self.mcp_servers_file, mcp_servers_data)

        return res

    def toggle_mcp(self, name: str, enable: bool) -> bool:
        mcps = self.list_mcps()
        target = next((m for m in mcps if m.name == name), None)
        if not target:
            return False
        target.enabled = enable
        return self.save_mcp(target)

    def delete_mcp(self, name: str) -> bool:
        settings_data = self.read_json_file(self.settings_file)
        modified = False
        if "mcpServers" in settings_data and name in settings_data["mcpServers"]:
            del settings_data["mcpServers"][name]
            modified = True
        if "_disabledMcpServers" in settings_data and name in settings_data["_disabledMcpServers"]:
            del settings_data["_disabledMcpServers"][name]
            modified = True

        if modified:
            self.write_json_file(self.settings_file, settings_data)
            # Sync mcp_servers.json
            mcp_servers_data = self.read_json_file(self.mcp_servers_file)
            if "mcpServers" in mcp_servers_data and name in mcp_servers_data["mcpServers"]:
                del mcp_servers_data["mcpServers"][name]
                self.write_json_file(self.mcp_servers_file, mcp_servers_data)
            return True
        return False

    def list_plugins_and_skills(self, project_path: Optional[str] = None) -> List[PluginSkill]:
        items: List[PluginSkill] = []
        skills_state = self.read_json_file(self.skills_state_file)
        disabled_skills = set(skills_state.get("disabled_skills", []))

        # 1. Extensions in ~/.gemini/extensions
        ext_enablement = self.read_json_file(self.extensions_file)
        if os.path.exists(self.extensions_dir):
            for entry in os.listdir(self.extensions_dir):
                entry_path = os.path.join(self.extensions_dir, entry)
                if os.path.isdir(entry_path) and not entry.startswith('.'):
                    enabled = entry in ext_enablement
                    items.append(PluginSkill(
                        name=entry,
                        kind="extension",
                        enabled=enabled,
                        source=f"~/.gemini/extensions/{entry}",
                        path=entry_path,
                        description=f"Antigravity CLI Extension ({entry})",
                        source_file=self.extensions_file
                    ))

        # 2. Skills in ~/.gemini/skills and ~/.gemini/config/skills
        skill_dirs = [
            (self.skills_dir, "~/.gemini/skills"),
            (self.config_skills_dir, "~/.gemini/config/skills")
        ]
        seen_skills = set()
        for base_s_dir, label in skill_dirs:
            if not os.path.exists(base_s_dir):
                continue
            for entry in os.listdir(base_s_dir):
                entry_path = os.path.join(base_s_dir, entry)
                if os.path.isdir(entry_path) and not entry.startswith('.'):
                    if entry in seen_skills:
                        continue
                    seen_skills.add(entry)
                    skill_md = os.path.join(entry_path, "SKILL.md")
                    title, desc = self.parse_skill_md(skill_md)
                    name = title if title else entry
                    enabled = (entry not in disabled_skills and name not in disabled_skills and not entry.endswith('.disabled'))
                    items.append(PluginSkill(
                        name=entry,
                        kind="skill",
                        enabled=enabled,
                        source=f"{label}/{entry}",
                        path=entry_path,
                        description=desc or f"Skill {entry}",
                        source_file=self.skills_state_file
                    ))

        # 3. Project-specific skills
        if project_path:
            items.extend(self.scan_project_skills(project_path))
        else:
            for p in self.get_known_projects():
                items.extend(self.scan_project_skills(p))

        return sorted(items, key=lambda x: (x.kind, x.name.lower()))

    def toggle_plugin_skill(self, item: PluginSkill, enable: bool) -> bool:
        if item.kind == "extension":
            ext_data = self.read_json_file(self.extensions_file)
            if enable:
                if item.name not in ext_data:
                    home_override = os.path.join(os.path.expanduser("~"), "*")
                    ext_data[item.name] = {"overrides": [home_override]}
            else:
                ext_data.pop(item.name, None)
            return self.write_json_file(self.extensions_file, ext_data)
        else: # skill
            skills_state = self.read_json_file(self.skills_state_file)
            disabled_skills = set(skills_state.get("disabled_skills", []))
            if enable:
                disabled_skills.discard(item.name)
            else:
                disabled_skills.add(item.name)
            skills_state["disabled_skills"] = sorted(list(disabled_skills))
            return self.write_json_file(self.skills_state_file, skills_state)

    def add_skill(self, name: str, description: str, instructions: str) -> bool:
        target_dir = self.skills_dir
        os.makedirs(target_dir, exist_ok=True)
        self.create_skill_folder(target_dir, name, description, instructions)
        return True

    def delete_plugin_skill(self, item: PluginSkill) -> bool:
        # If extension, remove from extension-enablement
        if item.kind == "extension":
            ext_data = self.read_json_file(self.extensions_file)
            ext_data.pop(item.name, None)
            self.write_json_file(self.extensions_file, ext_data)

        # Remove from state
        skills_state = self.read_json_file(self.skills_state_file)
        disabled_skills = set(skills_state.get("disabled_skills", []))
        disabled_skills.discard(item.name)
        skills_state["disabled_skills"] = sorted(list(disabled_skills))
        self.write_json_file(self.skills_state_file, skills_state)

        # Move folder to backup instead of hard delete
        if item.path and os.path.exists(item.path):
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
        return self.settings_file

    def get_raw_config(self) -> Dict[str, Any]:
        return self.read_json_file(self.settings_file)

    def save_raw_config(self, data: Dict[str, Any]) -> bool:
        return self.write_json_file(self.settings_file, data)
