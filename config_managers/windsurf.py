import os
import shutil
from typing import List, Dict, Any, Optional
from models.mcp import McpServer
from models.plugin import PluginSkill
from .base import BaseConfigManager

class WindsurfConfigManager(BaseConfigManager):
    AGENT_NAME = "Windsurf"

    def __init__(self):
        home = os.path.expanduser("~")
        self.codeium_dir = os.path.join(home, ".codeium")
        self.codeium_windsurf_dir = os.path.join(self.codeium_dir, "windsurf")
        self.windsurf_dir = os.path.join(home, ".windsurf")
        self.mcp_file = os.path.join(self.codeium_windsurf_dir, "mcp_config.json")
        self.alt_mcp_file = os.path.join(self.windsurf_dir, "mcp_config.json")
        self.skills_dir = os.path.join(self.codeium_windsurf_dir, "skills")
        self.alt_skills_dir = os.path.join(self.windsurf_dir, "skills")

    def _get_active_config_path(self) -> str:
        if os.path.exists(self.mcp_file):
            return self.mcp_file
        if os.path.exists(self.alt_mcp_file):
            return self.alt_mcp_file
        return self.mcp_file

    def is_installed(self) -> bool:
        """Detects if Windsurf is installed or present on the system."""
        if os.path.exists(self.codeium_windsurf_dir) and os.path.isdir(self.codeium_windsurf_dir):
            return True
        if os.path.exists(self.windsurf_dir) and os.path.isdir(self.windsurf_dir):
            return True
        if os.path.exists(self.mcp_file) or os.path.exists(self.alt_mcp_file):
            return True
        if shutil.which("windsurf"):
            return True
        return False

    def _get_shelved_path(self) -> str:
        return self.get_shelved_filepath(self._get_active_config_path())

    def list_mcps(self) -> List[McpServer]:
        servers: List[McpServer] = []
        seen = set()
        cfg_path = self._get_active_config_path()
        data = self.read_json_file(cfg_path)

        # Active servers
        active_dict = data.get("mcpServers", {})
        for name, cfg in active_dict.items():
            if isinstance(cfg, dict):
                seen.add(name)
                servers.append(self._dict_to_mcp(name, cfg, enabled=True, source_file=cfg_path))

        # Disabled servers (stored in _disabledMcpServers)
        disabled_dict = data.get("_disabledMcpServers", {})
        for name, cfg in disabled_dict.items():
            if isinstance(cfg, dict) and name not in seen:
                seen.add(name)
                servers.append(self._dict_to_mcp(name, cfg, enabled=False, source_file=cfg_path))

        # Shelved MCPs
        for sm in self.read_shelved_mcps(self._get_shelved_path()):
            if sm.name not in seen:
                seen.add(sm.name)
                servers.append(sm)

        return sorted(servers, key=lambda x: x.name.lower())

    def _dict_to_mcp(self, name: str, cfg: Dict[str, Any], enabled: bool, source_file: str) -> McpServer:
        url = cfg.get("serverUrl") or cfg.get("url", "")
        server_type = cfg.get("type", "")
        if not server_type:
            server_type = "http" if url else "stdio"

        return McpServer(
            name=name,
            server_type=server_type,
            command=cfg.get("command"),
            args=cfg.get("args", []),
            env=cfg.get("env", {}),
            url=url if url else None,
            headers=cfg.get("headers", {}),
            enabled=enabled,
            raw_data=cfg,
            source_file=source_file
        )

    def save_mcp(self, mcp: McpServer) -> bool:
        if getattr(mcp, 'shelved', False):
            self.delete_mcp(mcp.name)
            return self.write_shelved_mcp(self._get_shelved_path(), mcp)

        self.delete_shelved_mcp(self._get_shelved_path(), mcp.name)

        cfg_path = self._get_active_config_path()
        data = self.read_json_file(cfg_path)
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

        return self.write_json_file(cfg_path, data)

    def shelve_mcp(self, mcp: McpServer) -> bool:
        """Temporarily removes MCP from Windsurf config and stores in sidecar shelved file."""
        self.delete_mcp(mcp.name)
        return self.write_shelved_mcp(self._get_shelved_path(), mcp)

    def unshelve_mcp(self, mcp: McpServer) -> bool:
        """Restores a shelved MCP back into the active Windsurf config."""
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
        modified = False
        if "mcpServers" in data and name in data["mcpServers"]:
            del data["mcpServers"][name]
            modified = True
        if "_disabledMcpServers" in data and name in data["_disabledMcpServers"]:
            del data["_disabledMcpServers"][name]
            modified = True

        return self.write_json_file(cfg_path, data) if modified else False

    def list_plugins_and_skills(self, project_path: Optional[str] = None) -> List[PluginSkill]:
        items: List[PluginSkill] = []
        skill_dirs = [
            (self.skills_dir, "~/.codeium/windsurf/skills"),
            (self.alt_skills_dir, "~/.windsurf/skills")
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
                    is_enabled = not entry.endswith('.disabled')
                    items.append(PluginSkill(
                        name=entry,
                        kind="skill",
                        enabled=is_enabled,
                        source=f"{label}/{entry}",
                        path=entry_path,
                        description=desc or f"Skill {entry}",
                        source_file=base_s_dir
                    ))

        # Project-specific skills
        if project_path:
            items.extend(self.scan_project_skills(project_path))
        else:
            for p in self.get_known_projects():
                items.extend(self.scan_project_skills(p))

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
        target_dir = self.skills_dir if os.path.exists(self.codeium_windsurf_dir) else self.alt_skills_dir
        os.makedirs(target_dir, exist_ok=True)
        self.create_skill_folder(target_dir, name, description, instructions)
        return True

    def delete_plugin_skill(self, item: PluginSkill) -> bool:
        if item.path and os.path.exists(item.path):
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
        return False

    def get_raw_config_path(self) -> str:
        return self._get_active_config_path()

    def get_raw_config(self) -> Dict[str, Any]:
        return self.read_json_file(self._get_active_config_path())

    def save_raw_config(self, data: Dict[str, Any]) -> bool:
        return self.write_json_file(self._get_active_config_path(), data)
