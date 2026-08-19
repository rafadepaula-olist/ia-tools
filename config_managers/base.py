import os
import shutil
import datetime
import json
import json5
import re
from typing import Any, Dict, Optional, Tuple

class BaseConfigManager:
    BACKUP_DIR = os.path.expanduser("~/.ia-tools-backups")

    @classmethod
    def ensure_backup_dir(cls):
        os.makedirs(cls.BACKUP_DIR, exist_ok=True, mode=0o700)
        try:
            os.chmod(cls.BACKUP_DIR, 0o700)
        except OSError:
            pass

    @classmethod
    def backup_file(cls, filepath: str) -> Optional[str]:
        if not filepath or not os.path.exists(filepath):
            return None
        cls.ensure_backup_dir()
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = os.path.basename(filepath)
        backup_path = os.path.join(cls.BACKUP_DIR, f"{base_name}.{ts}.bak")
        try:
            shutil.copy2(filepath, backup_path)
            # Also keep a single local .bak
            local_bak = f"{filepath}.bak"
            shutil.copy2(filepath, local_bak)
            return backup_path
        except Exception as e:
            print(f"Warning: Failed to backup {filepath}: {e}")
            return None

    @classmethod
    def read_json_file(cls, filepath: str) -> Dict[str, Any]:
        if not os.path.exists(filepath):
            return {}
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content.strip():
                    return {}
                # Try standard json first, fallback to json5 for comments/trailing commas
                try:
                    return json.loads(content)
                except Exception:
                    return json5.loads(content)
        except Exception as e:
            print(f"Error reading JSON from {filepath}: {e}")
            return {}

    @classmethod
    def write_json_file(cls, filepath: str, data: Dict[str, Any], backup: bool = True) -> bool:
        try:
            if backup and os.path.exists(filepath):
                cls.backup_file(filepath)

            os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
            tmp_path = f"{filepath}.tmp"
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write("\n")

            # Atomic rename
            os.replace(tmp_path, filepath)
            return True
        except Exception as e:
            print(f"Error writing JSON to {filepath}: {e}")
            return False

    @classmethod
    def parse_skill_md(cls, skill_md_path: str) -> Tuple[str, str]:
        """Extracts (name, description) from SKILL.md YAML frontmatter."""
        if not os.path.exists(skill_md_path):
            return "", ""
        try:
            with open(skill_md_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # Frontmatter regex
            match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            name = ""
            desc = ""
            if match:
                yaml_block = match.group(1)
                name_m = re.search(r'^name:\s*(.+)$', yaml_block, re.MULTILINE)
                desc_m = re.search(r'^description:\s*(.+)$', yaml_block, re.MULTILINE)
                if name_m:
                    name = name_m.group(1).strip(' "\'')
                if desc_m:
                    desc = desc_m.group(1).strip(' "\'')
            if not desc:
                # First non-header line
                lines = [l.strip() for l in content.split('\n') if l.strip() and not l.startswith('#') and not l.startswith('---')]
                if lines:
                    desc = lines[0]
            return name, desc
        except Exception as e:
            print(f"Error reading skill {skill_md_path}: {e}")
            return "", ""

    @classmethod
    def get_known_projects(cls) -> list[str]:
        """Discovers active projects from Claude, Gemini and common directories."""
        home = os.path.expanduser("~")
        projects = set()

        # Claude projects
        claude_json = os.path.join(home, ".claude.json")
        if os.path.exists(claude_json):
            try:
                c_data = cls.read_json_file(claude_json)
                for p in c_data.get("projects", {}).keys():
                    if os.path.exists(p) and os.path.isdir(p) and p != home:
                        projects.add(os.path.abspath(p))
            except Exception:
                pass

        # Gemini projects
        gemini_projects = os.path.join(home, ".gemini", "projects.json")
        if os.path.exists(gemini_projects):
            try:
                g_data = cls.read_json_file(gemini_projects)
                for item in g_data.get("recentProjects", []):
                    p = item.get("path") if isinstance(item, dict) else item
                    if p and isinstance(p, str) and os.path.exists(p) and os.path.isdir(p) and p != home:
                        projects.add(os.path.abspath(p))
            except Exception:
                pass

        # Also add current workspace if valid
        ia_tools_dir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if os.path.exists(ia_tools_dir) and os.path.isdir(ia_tools_dir) and ia_tools_dir != home:
            projects.add(ia_tools_dir)

        return sorted(list(projects), key=lambda x: x.lower())

    @classmethod
    def scan_project_skills(cls, project_path: str) -> list:
        """Scans for skills within a specific project folder."""
        from models.plugin import PluginSkill
        skills: list[PluginSkill] = []
        if not project_path or not os.path.exists(project_path):
            return skills

        # Candidate skill subdirectories in the project
        candidate_dirs = [
            (os.path.join(project_path, ".agents", "skills"), ".agents/skills"),
            (os.path.join(project_path, ".gemini", "skills"), ".gemini/skills"),
            (os.path.join(project_path, ".claude", "skills"), ".claude/skills"),
            (os.path.join(project_path, ".opencode", "skills"), ".opencode/skills"),
            (os.path.join(project_path, ".codex", "skills"), ".codex/skills"),
            (os.path.join(project_path, ".windsurf", "skills"), ".windsurf/skills"),
            (os.path.join(project_path, ".cursor", "skills"), ".cursor/skills"),
            (os.path.join(project_path, "skills"), "skills")
        ]

        seen_names = set()
        for s_dir, label in candidate_dirs:
            if not os.path.exists(s_dir) or not os.path.isdir(s_dir):
                continue
            for entry in os.listdir(s_dir):
                entry_path = os.path.join(s_dir, entry)
                if os.path.isdir(entry_path) and not entry.startswith('.'):
                    if entry in seen_names:
                        continue
                    seen_names.add(entry)
                    skill_md = os.path.join(entry_path, "SKILL.md")
                    title, desc = cls.parse_skill_md(skill_md)
                    is_enabled = not entry.endswith('.disabled')
                    p_name = os.path.basename(project_path)
                    skills.append(PluginSkill(
                        name=entry,
                        kind="skill",
                        enabled=is_enabled,
                        source=f"PROJ [{p_name}]: {label}/{entry}",
                        path=entry_path,
                        description=desc or f"Skill do projeto {p_name} ({entry})",
                        source_file=s_dir,
                        metadata={"scope": "project", "project_path": project_path}
                    ))

        return skills

    @classmethod
    def create_skill_folder(cls, target_dir: str, name: str, description: str, instructions: str) -> str:
        name = name.strip()
        if not name or not re.match(r'^[a-zA-Z0-9_-]+$', name):
            raise ValueError(f"Invalid skill name '{name}'. Only alphanumeric characters, hyphens, and underscores are allowed.")

        target_dir_abs = os.path.abspath(target_dir)
        skill_dir = os.path.abspath(os.path.join(target_dir_abs, name))

        if not skill_dir.startswith(target_dir_abs + os.sep) and skill_dir != target_dir_abs:
            raise ValueError(f"Directory traversal detected: '{name}' is not within '{target_dir}'.")

        os.makedirs(skill_dir, exist_ok=True)
        skill_file = os.path.join(skill_dir, "SKILL.md")

        # Clean description and instructions
        clean_desc = description.replace("\r\n", " ").replace("\n", " ").replace('"', '\\"').strip()
        content = f"""---
name: {name}
description: "{clean_desc}"
---

# {name}

{instructions}
"""
        with open(skill_file, 'w', encoding='utf-8') as f:
            f.write(content)
        return skill_dir

    def convert_mcp_to_global(self, mcp) -> bool:
        """Converts a project-scoped MCP to global scope."""
        old_project_path = getattr(mcp, 'project_path', None)
        mcp.scope = "global"
        mcp.project_path = None
        if getattr(mcp, 'shelved', False) and hasattr(self, '_get_shelved_path'):
            shelved_path = self._get_shelved_path()
            self.delete_shelved_mcp(shelved_path, mcp.name, project_path=old_project_path)
            return self.write_shelved_mcp(shelved_path, mcp)
        if hasattr(self, 'save_mcp'):
            return self.save_mcp(mcp)
        return False

    @classmethod
    def get_shelved_filepath(cls, config_filepath: str) -> str:
        """Returns the sidecar shelved JSON filepath right next to the active config file."""
        return f"{config_filepath}.shelved"

    @classmethod
    def read_shelved_mcps(cls, shelved_filepath: str) -> list:
        from models.mcp import McpServer
        if not os.path.exists(shelved_filepath):
            return []
        data = cls.read_json_file(shelved_filepath)
        servers: list[McpServer] = []
        for key, item in data.items():
            if isinstance(item, dict):
                servers.append(McpServer.from_shelved_dict(item))
        return sorted(servers, key=lambda x: x.name.lower())

    @classmethod
    def write_shelved_mcp(cls, shelved_filepath: str, mcp) -> bool:
        data = cls.read_json_file(shelved_filepath) if os.path.exists(shelved_filepath) else {}
        key = f"{mcp.project_path}::{mcp.name}" if getattr(mcp, 'project_path', None) else mcp.name
        mcp.shelved = True
        mcp.shelved_at = datetime.datetime.now().isoformat()
        data[key] = mcp.to_shelved_dict()
        return cls.write_json_file(shelved_filepath, data, backup=False)

    @classmethod
    def remove_shelved_mcp(cls, shelved_filepath: str, mcp_name: str, project_path: Optional[str] = None):
        from models.mcp import McpServer
        if not os.path.exists(shelved_filepath):
            return None
        data = cls.read_json_file(shelved_filepath)
        key = f"{project_path}::{mcp_name}" if project_path else mcp_name

        item = data.pop(key, None)
        if not item and project_path:
            item = data.pop(mcp_name, None)
        elif not item and not project_path:
            for k in list(data.keys()):
                if k == mcp_name or k.endswith(f"::{mcp_name}"):
                    item = data.pop(k, None)
                    break

        if item:
            cls.write_json_file(shelved_filepath, data, backup=False)
            restored = McpServer.from_shelved_dict(item)
            restored.shelved = False
            restored.shelved_at = None
            return restored
        return None

    @classmethod
    def delete_shelved_mcp(cls, shelved_filepath: str, mcp_name: str, project_path: Optional[str] = None) -> bool:
        if not os.path.exists(shelved_filepath):
            return False
        data = cls.read_json_file(shelved_filepath)
        key = f"{project_path}::{mcp_name}" if project_path else mcp_name

        deleted = False
        if key in data:
            del data[key]
            deleted = True
        else:
            for k in list(data.keys()):
                if k == mcp_name or k.endswith(f"::{mcp_name}"):
                    del data[k]
                    deleted = True
                    break

        if deleted:
            return cls.write_json_file(shelved_filepath, data, backup=False)
        return False

    def is_installed(self) -> bool:
        """Determines if the agent tool or configuration is present on the user system."""
        return False


