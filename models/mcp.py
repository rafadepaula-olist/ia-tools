from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import json

@dataclass
class McpServer:
    name: str
    server_type: str = "stdio"  # stdio, sse, http, local, remote
    command: Optional[str] = None
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    url: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    shelved: bool = False
    shelved_at: Optional[str] = None
    scope: str = "global"  # 'global' or 'project'
    project_path: Optional[str] = None  # e.g. '/home/foo.bar'
    raw_data: Dict[str, Any] = field(default_factory=dict)
    source_file: str = ""

    @property
    def is_remote(self) -> bool:
        return bool(self.url or self.server_type in ("sse", "http", "remote"))

    @property
    def display_type(self) -> str:
        if self.is_remote:
            return self.server_type.upper() if self.server_type else "REMOTE"
        return "STDIO"

    @property
    def command_display(self) -> str:
        if self.is_remote:
            return self.url or ""
        parts = []
        if self.command:
            parts.append(str(self.command))
        if self.args:
            parts.extend([str(a) for a in self.args])
        return " ".join(parts)

    def to_antigravity_dict(self) -> Dict[str, Any]:
        """Convert to Antigravity format."""
        if self.is_remote:
            d = {}
            if self.server_type:
                d["type"] = self.server_type
            if self.url:
                d["url"] = self.url
            if self.headers:
                d["headers"] = self.headers
            return d
        else:
            d = {}
            if self.command:
                d["command"] = self.command
            if self.args:
                d["args"] = self.args
            if self.env:
                d["env"] = self.env
            return d

    def to_claude_dict(self) -> Dict[str, Any]:
        """Convert to Claude format."""
        if self.is_remote:
            d = {"type": self.server_type if self.server_type in ["sse", "http"] else "http"}
            if self.url:
                d["url"] = self.url
            if self.headers:
                d["headers"] = self.headers
            return d
        else:
            d = {"type": "stdio"}
            if self.command:
                d["command"] = self.command
            if self.args:
                d["args"] = self.args
            if self.env:
                d["env"] = self.env
            return d

    def to_opencode_dict(self) -> Dict[str, Any]:
        """Convert to OpenCode format."""
        d: Dict[str, Any] = {
            "type": "remote" if self.is_remote else "local",
            "enabled": self.enabled
        }
        if self.is_remote:
            if self.url:
                d["url"] = self.url
            if self.headers:
                d["headers"] = self.headers
        else:
            cmd_list = []
            if self.command:
                cmd_list.append(self.command)
            if self.args:
                cmd_list.extend(self.args)
            if cmd_list:
                d["command"] = cmd_list
            if self.env:
                d["environment"] = self.env
        return d

    def to_codex_dict(self) -> Dict[str, Any]:
        """Convert to Codex / OpenAI Agents MCP format."""
        if self.is_remote:
            d = {}
            if self.url:
                d["url"] = self.url
            if self.headers:
                d["headers"] = self.headers
            return d
        else:
            d = {"command": self.command or "npx"}
            if self.args:
                d["args"] = self.args
            if self.env:
                d["env"] = self.env
            return d

    def to_windsurf_dict(self) -> Dict[str, Any]:
        """Convert to Windsurf / Codeium MCP format."""
        if self.is_remote:
            d = {}
            if self.url:
                d["serverUrl"] = self.url
            if self.headers:
                d["headers"] = self.headers
            return d
        else:
            d = {"command": self.command or "npx"}
            if self.args:
                d["args"] = self.args
            if self.env:
                d["env"] = self.env
            return d

    def to_cursor_dict(self) -> Dict[str, Any]:
        """Convert to Cursor MCP format."""
        if self.is_remote:
            d = {}
            if self.url:
                d["url"] = self.url
            if self.headers:
                d["headers"] = self.headers
            return d
        else:
            d = {"command": self.command or "npx"}
            if self.args:
                d["args"] = self.args
            if self.env:
                d["env"] = self.env
            return d

    def to_shelved_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for shelved storage."""
        return {
            "name": self.name,
            "server_type": self.server_type,
            "command": self.command,
            "args": self.args,
            "env": self.env,
            "url": self.url,
            "headers": self.headers,
            "enabled": self.enabled,
            "shelved": True,
            "shelved_at": self.shelved_at,
            "scope": self.scope,
            "project_path": self.project_path,
            "raw_data": self.raw_data,
            "source_file": self.source_file
        }

    @classmethod
    def from_shelved_dict(cls, data: Dict[str, Any]) -> "McpServer":
        """Recreate McpServer instance from shelved dictionary."""
        return cls(
            name=data.get("name", ""),
            server_type=data.get("server_type", "stdio"),
            command=data.get("command"),
            args=data.get("args", []),
            env=data.get("env", {}),
            url=data.get("url"),
            headers=data.get("headers", {}),
            enabled=data.get("enabled", True),
            shelved=True,
            shelved_at=data.get("shelved_at"),
            scope=data.get("scope", "global"),
            project_path=data.get("project_path"),
            raw_data=data.get("raw_data", {}),
            source_file=data.get("source_file", "")
        )

