import os
import shutil
from typing import List, Dict, Any, Optional
from models.mcp import McpServer
from models.plugin import PluginSkill
from .base import BaseConfigManager

class AntigravityConfigManager(BaseConfigManager):
    AGENT_NAME = "Antigravity"

    def __init__(self, base_dir: Optional[str] = None):
        home = os.path.expanduser("~")
        self.gemini_dir = base_dir or os.path.join(home, ".gemini")
        self.config_dir = os.path.join(self.gemini_dir, "config")
        self.mcp_config_file = os.path.join(self.config_dir, "mcp_config.json")
        self.alt_mcp_config_file = os.path.join(self.gemini_dir, "mcp_config.json")
        self.settings_file = os.path.join(self.gemini_dir, "settings.json")
        self.mcp_servers_file = os.path.join(self.gemini_dir, "mcp_servers.json")
        self.extensions_file = os.path.join(self.gemini_dir, "extensions", "extension-enablement.json")
        self.extensions_dir = os.path.join(self.gemini_dir, "extensions")
        self.skills_dir = os.path.join(self.gemini_dir, "skills")
        self.config_skills_dir = os.path.join(self.gemini_dir, "config", "skills")
        self.skills_state_file = os.path.join(self.gemini_dir, "skills_state.json")
        self.projects_file = os.path.join(self.gemini_dir, "projects.json")

    def _get_active_config_path(self) -> str:
        if os.path.exists(self.mcp_config_file):
            return self.mcp_config_file
        if os.path.exists(self.alt_mcp_config_file):
            return self.alt_mcp_config_file
        if os.path.exists(self.settings_file):
            return self.settings_file
        if os.path.exists(self.mcp_servers_file):
            return self.mcp_servers_file
        if os.path.exists(self.config_dir):
            return self.mcp_config_file
        return self.settings_file

    def _get_shelved_path(self) -> str:
        return self.get_shelved_filepath(self._get_active_config_path())

    def list_mcps(self) -> List[McpServer]:
        servers: List[McpServer] = []
        seen = set()

        candidate_files = [
            self.mcp_config_file,
            self.alt_mcp_config_file,
            self.settings_file,
            self.mcp_servers_file
        ]

        for cfg_file in candidate_files:
            if not os.path.exists(cfg_file):
                continue
            data = self.read_json_file(cfg_file)

            # Active/configured MCPs in mcpServers
            active_dict = data.get("mcpServers", {})
            if not active_dict:
                active_dict = data.get("mcp_servers", {})

            for name, cfg in active_dict.items():
                if not isinstance(cfg, dict):
                    continue
                key = ("global", None, name)
                if key not in seen:
                    seen.add(key)
                    servers.append(self._dict_to_mcp(name, cfg, source_file=cfg_file))

            # Disabled MCPs (in _disabledMcpServers or disabledMcpServers)
            disabled_dict = data.get("_disabledMcpServers", {})
            if not disabled_dict:
                disabled_dict = data.get("disabledMcpServers", {})

            for name, cfg in disabled_dict.items():
                if not isinstance(cfg, dict):
                    continue
                key = ("global", None, name)
                if key not in seen:
                    seen.add(key)
                    servers.append(self._dict_to_mcp(name, cfg, enabled=False, source_file=cfg_file))

        # Project-scoped MCPs from projects.json if available
        if os.path.exists(self.projects_file):
            proj_data = self.read_json_file(self.projects_file)
            projects_dict = proj_data.get("projects", {})
            for proj_path in projects_dict.keys():
                if not os.path.isdir(proj_path):
                    continue
                proj_cfg_candidates = [
                    os.path.join(proj_path, ".agents", "mcp_config.json"),
                    os.path.join(proj_path, ".gemini", "config", "mcp_config.json"),
                    os.path.join(proj_path, ".gemini", "mcp_config.json"),
                    os.path.join(proj_path, ".gemini", "settings.json"),
                ]
                for p_cfg in proj_cfg_candidates:
                    if os.path.exists(p_cfg):
                        p_data = self.read_json_file(p_cfg)
                        p_mcps = p_data.get("mcpServers", {}) or p_data.get("mcp_servers", {})
                        for name, cfg in p_mcps.items():
                            if isinstance(cfg, dict):
                                key = ("project", proj_path, name)
                                if key not in seen:
                                    seen.add(key)
                                    servers.append(self._dict_to_mcp(
                                        name=name,
                                        cfg=cfg,
                                        scope="project",
                                        project_path=proj_path,
                                        source_file=p_cfg
                                    ))

        # Shelved / Temporarily Removed MCPs
        shelved_paths = {self._get_shelved_path(), self.get_shelved_filepath(self.settings_file)}
        for sh_path in shelved_paths:
            for sm in self.read_shelved_mcps(sh_path):
                key = (sm.scope, sm.project_path, sm.name)
                if key not in seen:
                    seen.add(key)
                    servers.append(sm)

        return sorted(servers, key=lambda x: (x.scope, x.name.lower(), x.project_path or ""))

    def _dict_to_mcp(
        self,
        name: str,
        cfg: Dict[str, Any],
        enabled: Optional[bool] = None,
        scope: str = "global",
        project_path: Optional[str] = None,
        source_file: str = ""
    ) -> McpServer:
        if enabled is None:
            if "disabled" in cfg:
                enabled = not bool(cfg["disabled"])
            elif "enabled" in cfg:
                enabled = bool(cfg["enabled"])
            else:
                enabled = True
        else:
            if "disabled" in cfg:
                enabled = not bool(cfg["disabled"])
            elif "enabled" in cfg:
                enabled = bool(cfg["enabled"])

        url = cfg.get("url") or cfg.get("serverUrl", "")
        headers = cfg.get("headers", {})
        command = cfg.get("command", "")
        args = cfg.get("args", [])
        env = cfg.get("env") or cfg.get("environment", {})
        server_type = cfg.get("type", "")

        if isinstance(args, str):
            args = [args]

        if not server_type:
            if url:
                server_type = "http" if not url.endswith("/sse") else "sse"
            else:
                server_type = "stdio"

        return McpServer(
            name=name,
            server_type=server_type,
            command=command if command else None,
            args=args if isinstance(args, list) else [],
            env=env if isinstance(env, dict) else {},
            url=url if url else None,
            headers=headers if isinstance(headers, dict) else {},
            enabled=enabled,
            scope=scope,
            project_path=project_path,
            raw_data=cfg,
            source_file=source_file
        )

    def save_mcp(self, mcp: McpServer, old_mcp: Optional[McpServer] = None) -> bool:
        if getattr(mcp, 'shelved', False):
            if old_mcp:
                self.delete_mcp(old_mcp.name, project_path=old_mcp.project_path)
            self.delete_mcp(mcp.name, project_path=mcp.project_path)
            return self.write_shelved_mcp(self._get_shelved_path(), mcp)

        # Ensure removed from shelved sidecar
        self.delete_shelved_mcp(self._get_shelved_path(), mcp.name, project_path=mcp.project_path)
        if old_mcp and (old_mcp.name != mcp.name or old_mcp.project_path != mcp.project_path):
            self.delete_shelved_mcp(self._get_shelved_path(), old_mcp.name, project_path=old_mcp.project_path)

        if old_mcp and old_mcp.name != mcp.name:
            self.delete_mcp(old_mcp.name, project_path=old_mcp.project_path)

        active_cfg = self._get_active_config_path()
        data = self.read_json_file(active_cfg)
        if "mcpServers" not in data:
            data["mcpServers"] = {}

        mcp_dict = mcp.to_antigravity_dict()
        mcp_dict["disabled"] = not mcp.enabled
        data["mcpServers"][mcp.name] = mcp_dict
        if "_disabledMcpServers" in data:
            data["_disabledMcpServers"].pop(mcp.name, None)
        if "disabledMcpServers" in data:
            data["disabledMcpServers"].pop(mcp.name, None)

        res = self.write_json_file(active_cfg, data)

        # Sync with settings.json and mcp_servers.json if they exist and are not the primary file
        if active_cfg != self.settings_file and os.path.exists(self.settings_file):
            s_data = self.read_json_file(self.settings_file)
            if "mcpServers" not in s_data:
                s_data["mcpServers"] = {}
            if "_disabledMcpServers" not in s_data:
                s_data["_disabledMcpServers"] = {}
            s_data["mcpServers"].pop(mcp.name, None)
            s_data["_disabledMcpServers"].pop(mcp.name, None)
            if mcp.enabled:
                s_data["mcpServers"][mcp.name] = mcp_dict
            else:
                s_data["_disabledMcpServers"][mcp.name] = mcp_dict
            self.write_json_file(self.settings_file, s_data)

        if active_cfg != self.mcp_servers_file and os.path.exists(self.mcp_servers_file):
            ms_data = self.read_json_file(self.mcp_servers_file)
            if "mcpServers" not in ms_data:
                ms_data["mcpServers"] = {}
            if "_disabledMcpServers" not in ms_data:
                ms_data["_disabledMcpServers"] = {}
            ms_data["mcpServers"].pop(mcp.name, None)
            ms_data["_disabledMcpServers"].pop(mcp.name, None)
            if mcp.enabled:
                ms_data["mcpServers"][mcp.name] = mcp_dict
            else:
                ms_data["_disabledMcpServers"][mcp.name] = mcp_dict
            self.write_json_file(self.mcp_servers_file, ms_data)

        return res

    def shelve_mcp(self, mcp: McpServer) -> bool:
        """Temporarily removes MCP from provider config and stores in sidecar shelved file."""
        self.delete_mcp(mcp.name, project_path=mcp.project_path)
        return self.write_shelved_mcp(self._get_shelved_path(), mcp)

    def unshelve_mcp(self, mcp: McpServer) -> bool:
        """Restores a shelved MCP back into the active provider config."""
        restored = self.remove_shelved_mcp(self._get_shelved_path(), mcp.name, project_path=mcp.project_path)
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

    def delete_mcp(self, name: str, project_path: Optional[str] = None) -> bool:
        self.delete_shelved_mcp(self._get_shelved_path(), name, project_path=project_path)
        self.delete_shelved_mcp(self.get_shelved_filepath(self.settings_file), name, project_path=project_path)

        modified = False
        candidates = [
            self.mcp_config_file,
            self.alt_mcp_config_file,
            self.settings_file,
            self.mcp_servers_file
        ]
        for cfg_file in candidates:
            if os.path.exists(cfg_file):
                data = self.read_json_file(cfg_file)
                file_mod = False
                for key in ["mcpServers", "mcp_servers", "_disabledMcpServers", "disabledMcpServers"]:
                    if key in data and name in data[key]:
                        del data[key][name]
                        file_mod = True
                if file_mod:
                    self.write_json_file(cfg_file, data)
                    modified = True
        return modified


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
        """Detects if Antigravity / Gemini CLI is installed or present on the system."""
        # 1. Check Gemini / Antigravity config directory and files
        if os.path.exists(self.gemini_dir) and os.path.isdir(self.gemini_dir):
            return True
        home = os.path.expanduser("~")
        if os.path.exists(os.path.join(home, ".antigravity")):
            return True
        if os.path.exists(os.path.join(home, ".antigravity-ide")):
            return True
        if os.path.exists(self.settings_file) or os.path.exists(self.mcp_servers_file):
            return True
        if os.path.exists(self.skills_dir) or os.path.exists(self.config_skills_dir):
            return True

        # 2. Check executables in PATH
        for cmd in ("antigravity", "gemini", "agy"):
            if shutil.which(cmd):
                return True

        return False

