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
