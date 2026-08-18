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
        os.makedirs(cls.BACKUP_DIR, exist_ok=True)

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

        # Also add current workspace if in user home
        ia_tools_dir = os.path.abspath("/home/rafael.paula/ia-tools")
        if os.path.exists(ia_tools_dir):
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
        skill_dir = os.path.join(target_dir, name)
        os.makedirs(skill_dir, exist_ok=True)
        skill_file = os.path.join(skill_dir, "SKILL.md")
        content = f"""---
name: {name}
description: {description}
---

# {name}

{instructions}
"""
        with open(skill_file, 'w', encoding='utf-8') as f:
            f.write(content)
        return skill_dir
