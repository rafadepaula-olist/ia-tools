import os
import shutil
from typing import List, Dict, Any, Optional
from models.mcp import McpServer
from models.plugin import PluginSkill
from .base import BaseConfigManager

class ClaudeConfigManager(BaseConfigManager):
    AGENT_NAME = "Claude"

    def __init__(self):
        home = os.path.expanduser("~")
        self.claude_json_file = os.path.join(home, ".claude.json")
        self.claude_dir = os.path.join(home, ".claude")
        self.settings_file = os.path.join(self.claude_dir, "settings.json")
        self.plugins_dir = os.path.join(self.claude_dir, "plugins")
        self.skills_dir = os.path.join(self.claude_dir, "skills")

    def _get_shelved_path(self) -> str:
        return self.get_shelved_filepath(self.claude_json_file)

    def list_mcps(self) -> List[McpServer]:
        servers: List[McpServer] = []
        seen = set()
        claude_data = self.read_json_file(self.claude_json_file)
        settings_data = self.read_json_file(self.settings_file)

        # 1. Global Active MCPs in ~/.claude.json
        active_global = claude_data.get("mcpServers", {})
        for name, cfg in active_global.items():
            if isinstance(cfg, dict):
                seen.add(("global", None, name))
                servers.append(self._dict_to_mcp(name, cfg, enabled=True, scope="global", source_file=self.claude_json_file))

        # 2. Global Disabled MCPs in ~/.claude.json or ~/.claude/settings.json
        disabled_global = claude_data.get("_disabledMcpServers", {})
        if not disabled_global:
            disabled_global = claude_data.get("disabledMcpServers", {})
        if not disabled_global:
            disabled_global = settings_data.get("_disabledMcpServers", {})

        for name, cfg in disabled_global.items():
            if isinstance(cfg, dict) and ("global", None, name) not in seen:
                seen.add(("global", None, name))
                servers.append(self._dict_to_mcp(name, cfg, enabled=False, scope="global", source_file=self.claude_json_file))

        # 3. Project-level MCPs in ~/.claude.json (e.g. ~/, ~/tiny/tinystack/tinyerp, etc.)
        projects = claude_data.get("projects", {})
        for proj_path, proj_data in projects.items():
            if not isinstance(proj_data, dict):
                continue
            
            proj_mcps = proj_data.get("mcpServers", {})
            for name, cfg in proj_mcps.items():
                if isinstance(cfg, dict):
                    seen.add(("project", proj_path, name))
                    servers.append(self._dict_to_mcp(
                        name=name,
                        cfg=cfg,
                        enabled=True,
                        scope="project",
                        project_path=proj_path,
                        source_file=self.claude_json_file
                    ))

            proj_disabled = proj_data.get("_disabledMcpServers", {})
            for name, cfg in proj_disabled.items():
                if isinstance(cfg, dict) and ("project", proj_path, name) not in seen:
                    seen.add(("project", proj_path, name))
                    servers.append(self._dict_to_mcp(
                        name=name,
                        cfg=cfg,
                        enabled=False,
                        scope="project",
                        project_path=proj_path,
                        source_file=self.claude_json_file
                    ))

        # 4. Cloud claude.ai MCPs (from ~/.claude/mcp-needs-auth-cache.json or remote settings)
        cloud_cache_file = os.path.join(self.claude_dir, "mcp-needs-auth-cache.json")
        cloud_urls = {
            "claude.ai Datadog": "https://mcp.datadoghq.com/api/unstable/mcp-server/mcp",
            "claude.ai Intercom": "https://mcp.intercom.com/mcp",
            "claude.ai HubSpot": "https://mcp.hubspot.com/anthropic",
            "claude.ai Figma": "https://mcp.figma.com/mcp",
            "claude.ai Asana": "https://mcp.asana.com/sse",
        }
        if os.path.exists(cloud_cache_file):
            cache_data = self.read_json_file(cloud_cache_file)
            for c_name in cache_data.keys():
                if c_name.startswith("claude.ai") and not any(s.name == c_name for s in servers):
                    c_url = cloud_urls.get(c_name, "")
                    servers.append(McpServer(
                        name=c_name,
                        server_type="http" if not c_url.endswith("/sse") else "sse",
                        url=c_url,
                        enabled=True,
                        scope="cloud",
                        project_path="claude.ai",
                        source_file=cloud_cache_file
                    ))

        # 5. Shelved / Temporarily Removed MCPs
        for sm in self.read_shelved_mcps(self._get_shelved_path()):
            key = (sm.scope, sm.project_path, sm.name)
            if key not in seen:
                seen.add(key)
                servers.append(sm)

        return sorted(servers, key=lambda x: (x.scope, x.name.lower(), x.project_path or ""))

    def _dict_to_mcp(
        self,
        name: str,
        cfg: Dict[str, Any],
        enabled: bool,
        scope: str = "global",
        project_path: Optional[str] = None,
        source_file: str = ""
    ) -> McpServer:
        server_type = cfg.get("type", "stdio")
        url = cfg.get("url", "")
        headers = cfg.get("headers", {})
        command = cfg.get("command", "")
        args = cfg.get("args", [])
        env = cfg.get("env", {})

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

        # Remove from shelved sidecar if previously shelved
        self.delete_shelved_mcp(self._get_shelved_path(), mcp.name, project_path=mcp.project_path)
        if old_mcp and (old_mcp.name != mcp.name or old_mcp.project_path != mcp.project_path):
            self.delete_shelved_mcp(self._get_shelved_path(), old_mcp.name, project_path=old_mcp.project_path)

        claude_data = self.read_json_file(self.claude_json_file)
        mcp_dict = mcp.to_claude_dict()

        # If old_mcp is provided and had a different name or project_path, remove the old entry
        if old_mcp:
            old_name = old_mcp.name
            old_proj = old_mcp.project_path
            if old_proj and "projects" in claude_data and old_proj in claude_data["projects"]:
                p_data = claude_data["projects"][old_proj]
                if "mcpServers" in p_data:
                    p_data["mcpServers"].pop(old_name, None)
                if "_disabledMcpServers" in p_data:
                    p_data["_disabledMcpServers"].pop(old_name, None)
            else:
                if "mcpServers" in claude_data:
                    claude_data["mcpServers"].pop(old_name, None)
                if "_disabledMcpServers" in claude_data:
                    claude_data["_disabledMcpServers"].pop(old_name, None)

        if mcp.project_path:
            if "projects" not in claude_data:
                claude_data["projects"] = {}
            if mcp.project_path not in claude_data["projects"]:
                claude_data["projects"][mcp.project_path] = {}
            
            p_data = claude_data["projects"][mcp.project_path]
            if "mcpServers" not in p_data:
                p_data["mcpServers"] = {}
            if "_disabledMcpServers" not in p_data:
                p_data["_disabledMcpServers"] = {}

            p_data["mcpServers"].pop(mcp.name, None)
            p_data["_disabledMcpServers"].pop(mcp.name, None)

            if mcp.enabled:
                p_data["mcpServers"][mcp.name] = mcp_dict
            else:
                p_data["_disabledMcpServers"][mcp.name] = mcp_dict
        else:
            if "mcpServers" not in claude_data:
                claude_data["mcpServers"] = {}
            if "_disabledMcpServers" not in claude_data:
                claude_data["_disabledMcpServers"] = {}

            claude_data["mcpServers"].pop(mcp.name, None)
            claude_data["_disabledMcpServers"].pop(mcp.name, None)

            if mcp.enabled:
                claude_data["mcpServers"][mcp.name] = mcp_dict
            else:
                claude_data["_disabledMcpServers"][mcp.name] = mcp_dict

        return self.write_json_file(self.claude_json_file, claude_data)

    def shelve_mcp(self, mcp: McpServer) -> bool:
        """Temporarily removes MCP from Claude config and stores in sidecar shelved file."""
        self.delete_mcp(mcp.name, project_path=mcp.project_path)
        return self.write_shelved_mcp(self._get_shelved_path(), mcp)

    def unshelve_mcp(self, mcp: McpServer) -> bool:
        """Restores a shelved MCP back into the active Claude config."""
        restored = self.remove_shelved_mcp(self._get_shelved_path(), mcp.name, project_path=mcp.project_path)
        if restored:
            restored.shelved = False
            restored.enabled = True
            return self.save_mcp(restored)
        mcp.shelved = False
        mcp.enabled = True
        return self.save_mcp(mcp)

    def convert_mcp_to_global(self, mcp: McpServer) -> bool:
        old_project_path = mcp.project_path
        if getattr(mcp, 'shelved', False):
            self.delete_shelved_mcp(self._get_shelved_path(), mcp.name, project_path=old_project_path)
            mcp.scope = "global"
            mcp.project_path = None
            return self.write_shelved_mcp(self._get_shelved_path(), mcp)

        claude_data = self.read_json_file(self.claude_json_file)

        # 1. Remove from project-level if it was scoped to a project
        if old_project_path and "projects" in claude_data and old_project_path in claude_data["projects"]:
            p_data = claude_data["projects"][old_project_path]
            if "mcpServers" in p_data:
                p_data["mcpServers"].pop(mcp.name, None)
            if "_disabledMcpServers" in p_data:
                p_data["_disabledMcpServers"].pop(mcp.name, None)

        # 2. Insert into root global mcpServers / _disabledMcpServers
        if "mcpServers" not in claude_data:
            claude_data["mcpServers"] = {}
        if "_disabledMcpServers" not in claude_data:
            claude_data["_disabledMcpServers"] = {}

        claude_data["mcpServers"].pop(mcp.name, None)
        claude_data["_disabledMcpServers"].pop(mcp.name, None)

        mcp_dict = mcp.to_claude_dict()
        if mcp.enabled:
            claude_data["mcpServers"][mcp.name] = mcp_dict
        else:
            claude_data["_disabledMcpServers"][mcp.name] = mcp_dict

        mcp.scope = "global"
        mcp.project_path = None

        return self.write_json_file(self.claude_json_file, claude_data)


    def toggle_mcp(self, name: str, enable: bool, project_path: Optional[str] = None) -> bool:
        mcps = self.list_mcps()
        target = next((m for m in mcps if m.name == name and m.project_path == project_path), None)
        if not target:
            target = next((m for m in mcps if m.name == name), None)
        if not target:
            return False
        target.enabled = enable
        return self.save_mcp(target)

    def delete_mcp(self, name: str, project_path: Optional[str] = None) -> bool:
        self.delete_shelved_mcp(self._get_shelved_path(), name, project_path=project_path)

        claude_data = self.read_json_file(self.claude_json_file)
        modified = False

        if project_path and "projects" in claude_data and project_path in claude_data["projects"]:
            p_data = claude_data["projects"][project_path]
            if "mcpServers" in p_data and name in p_data["mcpServers"]:
                del p_data["mcpServers"][name]
                modified = True
            if "_disabledMcpServers" in p_data and name in p_data["_disabledMcpServers"]:
                del p_data["_disabledMcpServers"][name]
                modified = True
        else:
            if "mcpServers" in claude_data and name in claude_data["mcpServers"]:
                del claude_data["mcpServers"][name]
                modified = True
            if "_disabledMcpServers" in claude_data and name in claude_data["_disabledMcpServers"]:
                del claude_data["_disabledMcpServers"][name]
                modified = True

        if modified:
            return self.write_json_file(self.claude_json_file, claude_data)
        return False

    def list_plugins_and_skills(self, project_path: Optional[str] = None) -> List[PluginSkill]:
        items: List[PluginSkill] = []
        settings_data = self.read_json_file(self.settings_file)
        enabled_plugins = settings_data.get("enabledPlugins", {})
        marketplaces = settings_data.get("extraKnownMarketplaces", {})

        seen_plugins = set()

        # 1. Registered plugins from settings.json
        for plug_id, is_enabled in enabled_plugins.items():
            seen_plugins.add(plug_id)
            # Find market or source info
            source_info = "Official Marketplace"
            if "@" in plug_id:
                name_part, mkt_part = plug_id.split("@", 1)
                if mkt_part in marketplaces:
                    src_obj = marketplaces[mkt_part].get("source", {})
                    source_info = src_obj.get("repo") or src_obj.get("url") or src_obj.get("path") or mkt_part
            else:
                name_part = plug_id

            items.append(PluginSkill(
                name=plug_id,
                kind="plugin",
                enabled=bool(is_enabled),
                source=source_info,
                path=os.path.join(self.plugins_dir, plug_id.replace("/", "_")),
                description=f"Claude Plugin: {plug_id}",
                source_file=self.settings_file
            ))

        # 2. Installed folders in ~/.claude/plugins
        if os.path.exists(self.plugins_dir):
            for entry in os.listdir(self.plugins_dir):
                entry_path = os.path.join(self.plugins_dir, entry)
                if os.path.isdir(entry_path) and not entry.startswith('.'):
                    if entry not in seen_plugins:
                        items.append(PluginSkill(
                            name=entry,
                            kind="plugin",
                            enabled=entry in enabled_plugins and enabled_plugins[entry],
                            source="~/.claude/plugins",
                            path=entry_path,
                            description=f"Installed plugin {entry}",
                            source_file=self.settings_file
                        ))

        # 3. Skills in ~/.claude/skills
        if os.path.exists(self.skills_dir):
            for entry in os.listdir(self.skills_dir):
                entry_path = os.path.join(self.skills_dir, entry)
                if os.path.isdir(entry_path) and not entry.startswith('.'):
                    skill_md = os.path.join(entry_path, "SKILL.md")
                    title, desc = self.parse_skill_md(skill_md)
                    # For Claude skills, check if disabled in settings
                    is_enabled = not entry.endswith('.disabled')
                    items.append(PluginSkill(
                        name=entry,
                        kind="skill",
                        enabled=is_enabled,
                        source="~/.claude/skills",
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
        if item.kind == "plugin":
            settings_data = self.read_json_file(self.settings_file)
            if "enabledPlugins" not in settings_data:
                settings_data["enabledPlugins"] = {}
            settings_data["enabledPlugins"][item.name] = enable
            return self.write_json_file(self.settings_file, settings_data)
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

    def add_plugin(self, plugin_id: str, marketplace_name: str = "", repo_or_url: str = "", source_type: str = "github") -> bool:
        settings_data = self.read_json_file(self.settings_file)
        if "enabledPlugins" not in settings_data:
            settings_data["enabledPlugins"] = {}
        settings_data["enabledPlugins"][plugin_id] = True

        if marketplace_name and repo_or_url:
            if "extraKnownMarketplaces" not in settings_data:
                settings_data["extraKnownMarketplaces"] = {}
            
            src_dict = {"source": source_type}
            if source_type == "github":
                src_dict["repo"] = repo_or_url
            elif source_type == "git":
                src_dict["url"] = repo_or_url
            elif source_type == "directory":
                src_dict["path"] = repo_or_url

            settings_data["extraKnownMarketplaces"][marketplace_name] = {"source": src_dict}

        return self.write_json_file(self.settings_file, settings_data)

    def add_skill(self, name: str, description: str, instructions: str) -> bool:
        target_dir = self.skills_dir
        os.makedirs(target_dir, exist_ok=True)
        self.create_skill_folder(target_dir, name, description, instructions)
        return True

    def delete_plugin_skill(self, item: PluginSkill) -> bool:
        if item.kind == "plugin":
            settings_data = self.read_json_file(self.settings_file)
            if "enabledPlugins" in settings_data and item.name in settings_data["enabledPlugins"]:
                del settings_data["enabledPlugins"][item.name]
                self.write_json_file(self.settings_file, settings_data)
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
        return self.claude_json_file

    def get_raw_config(self) -> Dict[str, Any]:
        return self.read_json_file(self.claude_json_file)

    def save_raw_config(self, data: Dict[str, Any]) -> bool:
        return self.write_json_file(self.claude_json_file, data)

    def is_installed(self) -> bool:
        """Detects if Claude Code is installed or present on the system."""
        # 1. Config files and directories
        if os.path.exists(self.claude_json_file) and os.path.isfile(self.claude_json_file):
            return True
        if os.path.exists(self.claude_dir) and os.path.isdir(self.claude_dir):
            return True
        if os.path.exists(self.settings_file) or os.path.exists(self.plugins_dir) or os.path.exists(self.skills_dir):
            return True

        # 2. Executables in PATH
        if shutil.which("claude"):
            return True

        return False

