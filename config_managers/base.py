import os
import sys
import shutil
import datetime
import tempfile
import json
import json5
import re
import urllib.parse
from typing import Any, Dict, Optional, Tuple

class BaseConfigManager:
    BACKUP_DIR = os.path.expanduser("~/.ia-tools-backups")
    MAX_BACKUPS_PER_FILE = 10
    MAX_BACKUP_AGE_DAYS = 30

    @classmethod
    def ensure_backup_dir(cls):
        os.makedirs(cls.BACKUP_DIR, exist_ok=True, mode=0o700)
        try:
            os.chmod(cls.BACKUP_DIR, 0o700)
        except OSError:
            pass

    @classmethod
    def prune_backups(cls):
        """Prunes backups older than MAX_BACKUP_AGE_DAYS or keeping only MAX_BACKUPS_PER_FILE per original config."""
        if not os.path.exists(cls.BACKUP_DIR):
            return
        now = datetime.datetime.now()
        cutoff = now - datetime.timedelta(days=cls.MAX_BACKUP_AGE_DAYS)
        file_groups: Dict[str, list] = {}

        try:
            for entry in os.listdir(cls.BACKUP_DIR):
                full_path = os.path.join(cls.BACKUP_DIR, entry)
                if not os.path.isfile(full_path) or not entry.endswith(".bak"):
                    continue

                mtime = datetime.datetime.fromtimestamp(os.path.getmtime(full_path))
                if mtime < cutoff:
                    try:
                        os.remove(full_path)
                    except OSError:
                        pass
                    continue

                parts = entry.rsplit(".", 2)
                prefix = parts[0] if len(parts) >= 3 else entry
                file_groups.setdefault(prefix, []).append((mtime, full_path))

            for prefix, backups in file_groups.items():
                if len(backups) > cls.MAX_BACKUPS_PER_FILE:
                    backups.sort(key=lambda x: x[0])
                    excess = len(backups) - cls.MAX_BACKUPS_PER_FILE
                    for _, old_path in backups[:excess]:
                        try:
                            os.remove(old_path)
                        except OSError:
                            pass
        except Exception as e:
            print(f"Error pruning backups: {e}")

    @classmethod
    def backup_file(cls, filepath: str) -> Optional[str]:
        if not filepath or not os.path.exists(filepath):
            return None
        cls.ensure_backup_dir()
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        bak_file = os.path.join(cls.BACKUP_DIR, f"{os.path.basename(filepath)}.{ts}.bak")
        try:
            shutil.copy2(filepath, bak_file)
            if hasattr(os, 'chmod') and os.name == 'posix':
                try:
                    os.chmod(bak_file, 0o600)
                except OSError:
                    pass
            cls.prune_backups()
            return bak_file
        except Exception as e:
            print(f"Error backing up {filepath}: {e}")
            return None

    @classmethod
    def read_json_file(cls, filepath: str) -> Dict[str, Any]:
        if not os.path.exists(filepath):
            return {}
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return {}
                try:
                    return json.loads(content)
                except Exception:
                    return json5.loads(content)
        except Exception as e:
            print(f"Error reading JSON/JSON5 file {filepath}: {e}")
            return {}

    @classmethod
    def write_json_file(cls, filepath: str, data: Dict[str, Any], backup: bool = True) -> bool:
        tmp_path = None
        try:
            if backup and os.path.exists(filepath):
                cls.backup_file(filepath)

            dir_path = os.path.dirname(os.path.abspath(filepath))
            os.makedirs(dir_path, exist_ok=True)

            fd, tmp_path = tempfile.mkstemp(prefix=".ia_tools_", suffix=".tmp", dir=dir_path)
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write("\n")
                f.flush()
                os.fsync(f.fileno())

            # Atomic rename
            os.replace(tmp_path, filepath)
            tmp_path = None

            # Ensure restrictive permissions (0o600) for credentials & tokens on POSIX
            if hasattr(os, 'chmod') and os.name == 'posix':
                try:
                    os.chmod(filepath, 0o600)
                except OSError:
                    pass
            return True
        except Exception as e:
            print(f"Error writing JSON to {filepath}: {e}")
            return False
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

    @classmethod
    def parse_skill_md(cls, skill_md_path: str) -> Tuple[str, str]:
        """Extracts (name, description) from SKILL.md YAML frontmatter."""
        if not os.path.exists(skill_md_path):
            return "", ""
        try:
            with open(skill_md_path, 'r', encoding='utf-8') as f:
                content = f.read()

            name = ""
            desc = ""
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]
                    for line in frontmatter.split('\n'):
                        line = line.strip()
                        if line.startswith('name:'):
                            name = line.split('name:', 1)[1].strip().strip('"\'')
                        elif line.startswith('description:'):
                            desc = line.split('description:', 1)[1].strip().strip('"\'')

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
    def is_valid_project_path(cls, path: Optional[str]) -> bool:
        """Validates if a given path is a valid workspace project directory across Linux, macOS and Windows."""
        if not path or not isinstance(path, str):
            return False

        path_str = path.strip()
        if not path_str or path_str in ("~", "/", "\\"):
            return False

        home = os.path.abspath(os.path.expanduser("~"))
        abs_path = os.path.abspath(os.path.expanduser(path_str))

        if abs_path == home or abs_path == "/" or not os.path.exists(abs_path) or not os.path.isdir(abs_path):
            return False

        # Reject Windows root drives (e.g., C:\, D:\)
        drive, tail = os.path.splitdrive(abs_path)
        if drive and tail in ("", "/", "\\", os.sep):
            return False

        # Exclude temporary PyInstaller and system mount directories
        if "_MEI" in abs_path:
            return False
        for s_prefix in ("/proc", "/sys", "/dev", "/run"):
            if abs_path == s_prefix or abs_path.startswith(s_prefix + os.sep):
                return False

        # Windows system folders
        win_dir = os.environ.get("WINDIR") or os.environ.get("SystemRoot")
        prog_files = os.environ.get("ProgramFiles")
        prog_files_x86 = os.environ.get("ProgramFiles(x86)")
        prog_data = os.environ.get("ProgramData")

        for w_prefix in (win_dir, prog_files, prog_files_x86, prog_data):
            if w_prefix:
                w_norm = os.path.abspath(w_prefix)
                if abs_path == w_norm or abs_path.startswith(w_norm + os.sep):
                    return False

        # Exclude hidden config/system folders in user home
        excluded_home_prefixes = (
            os.path.join(home, ".gemini"),
            os.path.join(home, ".claude"),
            os.path.join(home, ".config"),
            os.path.join(home, ".agents"),
            os.path.join(home, ".antigravity"),
            os.path.join(home, ".antigravity-ide"),
            os.path.join(home, ".opencode"),
            os.path.join(home, ".codex"),
            os.path.join(home, ".windsurf"),
            os.path.join(home, ".cursor"),
            os.path.join(home, ".litellm"),
            os.path.join(home, ".local"),
            os.path.join(home, ".cache"),
            os.path.join(home, ".ssh"),
            os.path.join(home, ".var"),
            os.path.join(home, ".gnupg"),
            os.path.join(home, "AppData", "Local", "Temp"),
        )
        for prefix in excluded_home_prefixes:
            if abs_path == prefix or abs_path.startswith(prefix + os.sep):
                return False

        return True

    @classmethod
    def get_known_projects(cls) -> list[str]:
        """Returns explicitly registered projects saved by the user in ia-tools configuration."""
        home = os.path.expanduser("~")
        projects = set()

        # Load from ia-tools persistence
        ia_tools_cfg = os.path.join(home, ".config", "ia-tools", "projects.json")
        if os.path.exists(ia_tools_cfg):
            try:
                data = cls.read_json_file(ia_tools_cfg)
                if isinstance(data, list):
                    for p in data:
                        if cls.is_valid_project_path(p):
                            projects.add(os.path.abspath(os.path.expanduser(p)))
            except Exception:
                pass

        # Also add current workspace if running from source in development
        if not getattr(sys, 'frozen', False):
            ia_tools_dir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            if cls.is_valid_project_path(ia_tools_dir):
                projects.add(ia_tools_dir)

        return sorted(list(projects))

    @classmethod
    def register_known_project(cls, path: str) -> None:
        """Persists a new project path added by user in ~/.config/ia-tools/projects.json."""
        if not cls.is_valid_project_path(path):
            return
        abs_p = os.path.abspath(os.path.expanduser(path))
        projects = set(cls.get_known_projects())
        projects.add(abs_p)
        home = os.path.expanduser("~")
        ia_tools_dir = os.path.join(home, ".config", "ia-tools")
        os.makedirs(ia_tools_dir, exist_ok=True)
        cls.write_json_file(os.path.join(ia_tools_dir, "projects.json"), sorted(list(projects)))

    @classmethod
    def scan_project_skills(cls, project_path: str) -> list:
        """Scans for skills within a specific project folder."""
        from models.plugin import PluginSkill
        skills: list[PluginSkill] = []
        if not cls.is_valid_project_path(project_path):
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


