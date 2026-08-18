import os
import shutil
from typing import List, Dict, Any, Optional
from models.mcp import McpServer
from models.plugin import PluginSkill
from .base import BaseConfigManager

class ClaudeConfigManager(BaseConfigManager):
    def __init__(self):
        home = os.path.expanduser("~")
        self.claude_json_file = os.path.join(home, ".claude.json")
        self.claude_dir = os.path.join(home, ".claude")
        self.settings_file = os.path.join(self.claude_dir, "settings.json")
        self.plugins_dir = os.path.join(self.claude_dir, "plugins")
        self.skills_dir = os.path.join(self.claude_dir, "skills")

    def list_mcps(self) -> List[McpServer]:
        servers: List[McpServer] = []
        seen = set()

        claude_data = self.read_json_file(self.claude_json_file)
        settings_data = self.read_json_file(self.settings_file)

        # Active MCPs in ~/.claude.json
        active_dict = claude_data.get("mcpServers", {})
        for name, cfg in active_dict.items():
            if not isinstance(cfg, dict):
                continue
            seen.add(name)
            servers.append(self._dict_to_mcp(name, cfg, enabled=True, source_file=self.claude_json_file))

        # Disabled MCPs in ~/.claude.json or ~/.claude/settings.json
        disabled_dict = claude_data.get("_disabledMcpServers", {})
        if not disabled_dict:
            disabled_dict = claude_data.get("disabledMcpServers", {})
        if not disabled_dict:
            disabled_dict = settings_data.get("_disabledMcpServers", {})

        for name, cfg in disabled_dict.items():
            if name in seen or not isinstance(cfg, dict):
                continue
            seen.add(name)
            servers.append(self._dict_to_mcp(name, cfg, enabled=False, source_file=self.claude_json_file))

        return sorted(servers, key=lambda x: x.name.lower())

    def _dict_to_mcp(self, name: str, cfg: Dict[str, Any], enabled: bool, source_file: str) -> McpServer:
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
            raw_data=cfg,
            source_file=source_file
        )

    def save_mcp(self, mcp: McpServer) -> bool:
        claude_data = self.read_json_file(self.claude_json_file)
        if "mcpServers" not in claude_data:
            claude_data["mcpServers"] = {}
        if "_disabledMcpServers" not in claude_data:
            claude_data["_disabledMcpServers"] = {}

        # Remove from both
        claude_data["mcpServers"].pop(mcp.name, None)
        claude_data["_disabledMcpServers"].pop(mcp.name, None)

        mcp_dict = mcp.to_claude_dict()

        if mcp.enabled:
            claude_data["mcpServers"][mcp.name] = mcp_dict
        else:
            claude_data["_disabledMcpServers"][mcp.name] = mcp_dict

        return self.write_json_file(self.claude_json_file, claude_data)

    def toggle_mcp(self, name: str, enable: bool) -> bool:
        mcps = self.list_mcps()
        target = next((m for m in mcps if m.name == name), None)
        if not target:
            return False
        target.enabled = enable
        return self.save_mcp(target)

    def delete_mcp(self, name: str) -> bool:
        claude_data = self.read_json_file(self.claude_json_file)
        modified = False
        if "mcpServers" in claude_data and name in claude_data["mcpServers"]:
            del claude_data["mcpServers"][name]
            modified = True
        if "_disabledMcpServers" in claude_data and name in claude_data["_disabledMcpServers"]:
            del claude_data["_disabledMcpServers"][name]
            modified = True

        if modified:
            return self.write_json_file(self.claude_json_file, claude_data)
        return False

    def list_plugins_and_skills(self) -> List[PluginSkill]:
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
