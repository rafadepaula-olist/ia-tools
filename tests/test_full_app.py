import unittest
import os
import sys
import shutil
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_managers import (
    AntigravityConfigManager, ClaudeConfigManager, OpenCodeConfigManager,
    CodexConfigManager, WindsurfConfigManager, CursorConfigManager, BaseConfigManager
)
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

        # Codex conversion
        cd_dict = mcp_stdio.to_codex_dict()
        self.assertEqual(cd_dict["command"], "npx")
        self.assertEqual(cd_dict["args"][0], "-y")
        self.assertEqual(cd_dict["env"]["DEBUG"], "true")

        # Windsurf conversion
        ws_dict = mcp_stdio.to_windsurf_dict()
        self.assertEqual(ws_dict["command"], "npx")
        self.assertEqual(ws_dict["args"][0], "-y")
        self.assertEqual(ws_dict["env"]["DEBUG"], "true")

        # Cursor conversion
        cs_dict = mcp_stdio.to_cursor_dict()
        self.assertEqual(cs_dict["command"], "npx")
        self.assertEqual(cs_dict["args"][0], "-y")
        self.assertEqual(cs_dict["env"]["DEBUG"], "true")

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

        cd_dict = mcp_remote.to_codex_dict()
        self.assertEqual(cd_dict["url"], "https://mcp.example.com/sse")
        self.assertEqual(cd_dict["headers"]["Authorization"], "Bearer token123")

        ws_dict = mcp_remote.to_windsurf_dict()
        self.assertEqual(ws_dict["serverUrl"], "https://mcp.example.com/sse")
        self.assertEqual(ws_dict["headers"]["Authorization"], "Bearer token123")

        cs_dict = mcp_remote.to_cursor_dict()
        self.assertEqual(cs_dict["url"], "https://mcp.example.com/sse")
        self.assertEqual(cs_dict["headers"]["Authorization"], "Bearer token123")


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

    def test_base_is_installed(self):
        base_mgr = BaseConfigManager()
        self.assertFalse(base_mgr.is_installed())

    def test_detection_custom_paths(self):
        # 1. Antigravity custom path detection
        ag = AntigravityConfigManager()
        fake_gemini_dir = os.path.join(self.tmp_dir, "fake_gemini")
        ag.gemini_dir = fake_gemini_dir
        ag.settings_file = os.path.join(fake_gemini_dir, "settings.json")
        ag.mcp_servers_file = os.path.join(fake_gemini_dir, "mcp_servers.json")
        ag.skills_dir = os.path.join(fake_gemini_dir, "skills")
        ag.config_skills_dir = os.path.join(fake_gemini_dir, "config", "skills")

        # When directory doesn't exist (assuming CLI not in PATH or test path check)
        # Create directory -> should detect True
        os.makedirs(fake_gemini_dir, exist_ok=True)
        self.assertTrue(ag.is_installed())

        # 2. Claude custom path detection
        cl = ClaudeConfigManager()
        fake_claude_json = os.path.join(self.tmp_dir, "fake_claude.json")
        fake_claude_dir = os.path.join(self.tmp_dir, "fake_claude")
        cl.claude_json_file = fake_claude_json
        cl.claude_dir = fake_claude_dir
        cl.settings_file = os.path.join(fake_claude_dir, "settings.json")
        cl.plugins_dir = os.path.join(fake_claude_dir, "plugins")
        cl.skills_dir = os.path.join(fake_claude_dir, "skills")

        with open(fake_claude_json, "w") as f:
            f.write("{}")
        self.assertTrue(cl.is_installed())

        # 3. OpenCode custom path detection
        oc = OpenCodeConfigManager()
        fake_opencode_dir = os.path.join(self.tmp_dir, "fake_opencode")
        oc.config_dir = fake_opencode_dir
        oc.jsonc_file = os.path.join(fake_opencode_dir, "opencode.jsonc")
        oc.json_file = os.path.join(fake_opencode_dir, "opencode.json")
        oc.plugins_dir = os.path.join(fake_opencode_dir, "plugins")
        oc.skills_dir = os.path.join(fake_opencode_dir, "skills")

        os.makedirs(fake_opencode_dir, exist_ok=True)
        self.assertTrue(oc.is_installed())

        # 4. Codex custom path detection
        cd = CodexConfigManager()
        fake_codex_dir = os.path.join(self.tmp_dir, "fake_codex")
        cd.codex_dir = fake_codex_dir
        cd.config_file = os.path.join(fake_codex_dir, "config.json")
        cd.agents_dir = os.path.join(self.tmp_dir, "fake_agents")
        cd.agents_config_file = os.path.join(cd.agents_dir, "config.json")
        cd.skills_dir = os.path.join(fake_codex_dir, "skills")
        cd.agents_skills_dir = os.path.join(cd.agents_dir, "skills")

        os.makedirs(fake_codex_dir, exist_ok=True)
        self.assertTrue(cd.is_installed())

        # 5. Windsurf custom path detection
        ws = WindsurfConfigManager()
        fake_codeium_dir = os.path.join(self.tmp_dir, "fake_codeium")
        ws.codeium_dir = fake_codeium_dir
        ws.codeium_windsurf_dir = os.path.join(fake_codeium_dir, "windsurf")
        ws.windsurf_dir = os.path.join(self.tmp_dir, "fake_windsurf")
        ws.mcp_file = os.path.join(ws.codeium_windsurf_dir, "mcp_config.json")
        ws.alt_mcp_file = os.path.join(ws.windsurf_dir, "mcp_config.json")
        ws.skills_dir = os.path.join(ws.codeium_windsurf_dir, "skills")
        ws.alt_skills_dir = os.path.join(ws.windsurf_dir, "skills")

        os.makedirs(ws.codeium_windsurf_dir, exist_ok=True)
        self.assertTrue(ws.is_installed())

        # 6. Cursor custom path detection
        cs = CursorConfigManager()
        fake_cursor_dir = os.path.join(self.tmp_dir, "fake_cursor")
        cs.cursor_dir = fake_cursor_dir
        cs.config_cursor_dir = os.path.join(self.tmp_dir, "fake_config_cursor")
        cs.mcp_file = os.path.join(fake_cursor_dir, "mcp.json")
        cs.alt_mcp_file = os.path.join(cs.config_cursor_dir, "mcp.json")
        cs.skills_dir = os.path.join(fake_cursor_dir, "skills")
        cs.extensions_dir = os.path.join(fake_cursor_dir, "extensions")

        os.makedirs(fake_cursor_dir, exist_ok=True)
        self.assertTrue(cs.is_installed())

    def test_main_window_discovery_flow(self):
        from PyQt6.QtWidgets import QApplication
        from ui.main_window import MainWindow

        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        app = QApplication.instance() or QApplication([])
        win = MainWindow()

        # Test with original state (discovered count >= 1)
        self.assertGreaterEqual(win.main_tabs.count(), 1)

        # Mock: Only Claude detected
        orig_ag = AntigravityConfigManager.is_installed
        orig_cl = ClaudeConfigManager.is_installed
        orig_oc = OpenCodeConfigManager.is_installed
        orig_cd = CodexConfigManager.is_installed
        orig_ws = WindsurfConfigManager.is_installed
        orig_cs = CursorConfigManager.is_installed
        try:
            AntigravityConfigManager.is_installed = lambda self: False
            ClaudeConfigManager.is_installed = lambda self: True
            OpenCodeConfigManager.is_installed = lambda self: False
            CodexConfigManager.is_installed = lambda self: False
            WindsurfConfigManager.is_installed = lambda self: False
            CursorConfigManager.is_installed = lambda self: False

            win.discover_agents()
            self.assertEqual(win.main_tabs.count(), 1)
            self.assertIn("Claude", win.main_tabs.tabText(0))
            self.assertIn("Claude", win.managers)
            self.assertNotIn("Antigravity", win.managers)
            self.assertNotIn("OpenCode", win.managers)
            self.assertNotIn("Codex", win.managers)
            self.assertNotIn("Windsurf", win.managers)
            self.assertNotIn("Cursor", win.managers)

            # Mock: None detected (Empty State)
            ClaudeConfigManager.is_installed = lambda self: False
            win.discover_agents()
            self.assertEqual(win.main_tabs.count(), 1)
            self.assertIn("Nenhum", win.main_tabs.tabText(0))
            self.assertEqual(len(win.managers), 0)

            # Force all tabs (6 providers)
            win.discover_agents(force_all=True)
            self.assertEqual(win.main_tabs.count(), 6)
            self.assertEqual(len(win.managers), 6)
        finally:
            AntigravityConfigManager.is_installed = orig_ag
            ClaudeConfigManager.is_installed = orig_cl
            OpenCodeConfigManager.is_installed = orig_oc
            CodexConfigManager.is_installed = orig_cd
            WindsurfConfigManager.is_installed = orig_ws
            CursorConfigManager.is_installed = orig_cs

    def test_claude_convert_mcp_to_global(self):
        cl = ClaudeConfigManager()
        fake_claude_json = os.path.join(self.tmp_dir, "test_claude.json")
        cl.claude_json_file = fake_claude_json

        proj_path = "/home/user/myproject"
        proj_mcp = McpServer(
            name="test-project-mcp",
            server_type="stdio",
            command="npx",
            args=["-y", "test-pkg"],
            enabled=True,
            scope="project",
            project_path=proj_path
        )

        # 1. Save as project MCP
        self.assertTrue(cl.save_mcp(proj_mcp))
        data_before = cl.read_json_file(fake_claude_json)
        self.assertIn("projects", data_before)
        self.assertIn(proj_path, data_before["projects"])
        self.assertIn("test-project-mcp", data_before["projects"][proj_path]["mcpServers"])
        self.assertNotIn("test-project-mcp", data_before.get("mcpServers", {}))

        # 2. Convert to global
        self.assertTrue(cl.convert_mcp_to_global(proj_mcp))
        self.assertEqual(proj_mcp.scope, "global")
        self.assertIsNone(proj_mcp.project_path)

        data_after = cl.read_json_file(fake_claude_json)
        self.assertIn("test-project-mcp", data_after["mcpServers"])
        self.assertNotIn("test-project-mcp", data_after["projects"][proj_path].get("mcpServers", {}))

    def test_claude_save_mcp_scope_transition(self):
        cl = ClaudeConfigManager()
        fake_claude_json = os.path.join(self.tmp_dir, "test_claude_trans.json")
        cl.claude_json_file = fake_claude_json

        proj_path = "/home/user/scoped_project"
        old_mcp = McpServer(
            name="transition-mcp",
            server_type="stdio",
            command="uvx",
            args=["tool-pkg"],
            enabled=True,
            scope="project",
            project_path=proj_path
        )
        cl.save_mcp(old_mcp)

        new_mcp = McpServer(
            name="transition-mcp",
            server_type="stdio",
            command="uvx",
            args=["tool-pkg"],
            enabled=True,
            scope="global",
            project_path=None
        )
        self.assertTrue(cl.save_mcp(new_mcp, old_mcp=old_mcp))

        data = cl.read_json_file(fake_claude_json)
        self.assertIn("transition-mcp", data.get("mcpServers", {}))
        self.assertNotIn("transition-mcp", data.get("projects", {}).get(proj_path, {}).get("mcpServers", {}))

    def test_cross_provider_mcp_copying(self):
        ag = AntigravityConfigManager()
        fake_gemini_dir = os.path.join(self.tmp_dir, "gemini_copy_test")
        os.makedirs(fake_gemini_dir, exist_ok=True)
        ag.settings_file = os.path.join(fake_gemini_dir, "settings.json")
        ag.mcp_servers_file = os.path.join(fake_gemini_dir, "mcp_servers.json")

        source_mcp = McpServer(
            name="shared-service",
            server_type="http",
            url="https://mcp.service.com/sse",
            headers={"Authorization": "Bearer key123"},
            enabled=True,
            scope="global"
        )

        # Copy to Antigravity
        self.assertTrue(ag.save_mcp(source_mcp))
        ag_mcps = ag.list_mcps()
        self.assertEqual(len(ag_mcps), 1)
        self.assertEqual(ag_mcps[0].name, "shared-service")
        self.assertEqual(ag_mcps[0].url, "https://mcp.service.com/sse")
        self.assertEqual(ag_mcps[0].headers.get("Authorization"), "Bearer key123")

if __name__ == '__main__':
    unittest.main()




