from dataclasses import dataclass, field
from typing import Optional, Dict, Any

@dataclass
class PluginSkill:
    name: str
    kind: str = "plugin"  # 'plugin', 'skill', 'extension'
    enabled: bool = True
    source: str = ""       # Git URL, marketplace package, npm path, local directory
    path: str = ""         # Local filesystem path
    description: str = ""  # Extracted from SKILL.md or package.json
    source_file: str = ""   # Config file where this is tracked
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def display_kind(self) -> str:
        return self.kind.upper()

    @property
    def display_source(self) -> str:
        if self.source:
            return self.source
        if self.path:
            return self.path
        return "Local"
