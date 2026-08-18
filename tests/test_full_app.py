import unittest
import os
import sys
import shutil
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_managers import AntigravityConfigManager, ClaudeConfigManager, OpenCodeConfigManager, BaseConfigManager
from models import McpServer, PluginSkill

class TestFullIntegration(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_mcp_conversions(self):
        mcp_stdio = McpServer(
            name="test-stdio",
            server_type="stdio",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-postgres", "postgresql://localhost:5432"],
            env={"DEBUG": "true"},
            enabled=True
        )

        # Antigravity conversion
        ag_dict = mcp_stdio.to_antigravity_dict()
        self.assertEqual(ag_dict["command"], "npx")
        self.assertEqual(ag_dict["args"][0], "-y")
        self.assertEqual(ag_dict["env"]["DEBUG"], "true")

        # Claude conversion
        cl_dict = mcp_stdio.to_claude_dict()
        self.assertEqual(cl_dict["type"], "stdio")
        self.assertEqual(cl_dict["command"], "npx")

        # OpenCode conversion
        oc_dict = mcp_stdio.to_opencode_dict()
        self.assertEqual(oc_dict["type"], "local")
        self.assertEqual(oc_dict["enabled"], True)
        self.assertEqual(oc_dict["command"][0], "npx")
        self.assertEqual(oc_dict["environment"]["DEBUG"], "true")

    def test_mcp_remote_conversions(self):
        mcp_remote = McpServer(
            name="test-remote",
            server_type="http",
            url="https://mcp.example.com/sse",
            headers={"Authorization": "Bearer token123"},
            enabled=False
        )

        ag_dict = mcp_remote.to_antigravity_dict()
        self.assertEqual(ag_dict["url"], "https://mcp.example.com/sse")
        self.assertEqual(ag_dict["headers"]["Authorization"], "Bearer token123")

        cl_dict = mcp_remote.to_claude_dict()
        self.assertEqual(cl_dict["url"], "https://mcp.example.com/sse")

        oc_dict = mcp_remote.to_opencode_dict()
        self.assertEqual(oc_dict["type"], "remote")
        self.assertEqual(oc_dict["enabled"], False)
        self.assertEqual(oc_dict["url"], "https://mcp.example.com/sse")

    def test_skill_frontmatter_parser(self):
        test_skill_dir = os.path.join(self.tmp_dir, "my-skill")
        os.makedirs(test_skill_dir)
        skill_file = os.path.join(test_skill_dir, "SKILL.md")
        with open(skill_file, "w") as f:
            f.write("""---
name: my-skill
description: Tests database query optimizer
---

# Instructions
Do not optimize without explain plan.
""")
        name, desc = AntigravityConfigManager.parse_skill_md(skill_file)
        self.assertEqual(name, "my-skill")
        self.assertEqual(desc, "Tests database query optimizer")

    def test_create_skill_folder_security(self):
        target_dir = os.path.join(self.tmp_dir, "skills")
        os.makedirs(target_dir)

        # 1. Valid creation
        skill_path = BaseConfigManager.create_skill_folder(target_dir, "valid-skill", "My description", "Rules here")
        self.assertTrue(os.path.exists(os.path.join(skill_path, "SKILL.md")))

        # 2. Rejects path traversal
        with self.assertRaises(ValueError):
            BaseConfigManager.create_skill_folder(target_dir, "../../escaped-skill", "desc", "rules")

        with self.assertRaises(ValueError):
            BaseConfigManager.create_skill_folder(target_dir, "/etc/passwd", "desc", "rules")

        with self.assertRaises(ValueError):
            BaseConfigManager.create_skill_folder(target_dir, "invalid name with spaces!", "desc", "rules")

if __name__ == '__main__':
    unittest.main()
