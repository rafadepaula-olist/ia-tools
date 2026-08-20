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
        fake_gemini_dir = os.path.join(self.tmp_dir, "gemini_copy_test")
        os.makedirs(fake_gemini_dir, exist_ok=True)
        ag = AntigravityConfigManager(base_dir=fake_gemini_dir)

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

    def test_shelved_mcp_lifecycle(self):
        # 1. Test Antigravity Shelving with sidecar file
        fake_gemini_dir = os.path.join(self.tmp_dir, "gemini_shelve_test")
        os.makedirs(fake_gemini_dir, exist_ok=True)
        ag = AntigravityConfigManager(base_dir=fake_gemini_dir)

        mcp1 = McpServer(
            name="heavy-mcp",
            server_type="stdio",
            command="npx",
            args=["-y", "heavy-tool"],
            enabled=True
        )
        ag.save_mcp(mcp1)
        self.assertEqual(len(ag.list_mcps()), 1)
        self.assertFalse(ag.list_mcps()[0].shelved)

        # Shelve mcp1
        self.assertTrue(ag.shelve_mcp(mcp1))
        
        # Verify it is completely removed from settings.json and mcp_servers.json
        s_data = ag.read_json_file(ag.settings_file)
        self.assertNotIn("heavy-mcp", s_data.get("mcpServers", {}))
        self.assertNotIn("heavy-mcp", s_data.get("_disabledMcpServers", {}))

        # Verify sidecar file was created alongside settings.json
        sidecar_path = ag._get_shelved_path()
        self.assertTrue(os.path.exists(sidecar_path))
        
        # Verify list_mcps returns it with shelved=True
        mcps_after_shelve = ag.list_mcps()
        self.assertEqual(len(mcps_after_shelve), 1)
        self.assertTrue(mcps_after_shelve[0].shelved)
        self.assertEqual(mcps_after_shelve[0].name, "heavy-mcp")

        # Unshelve mcp1
        self.assertTrue(ag.unshelve_mcp(mcps_after_shelve[0]))
        mcps_restored = ag.list_mcps()
        self.assertEqual(len(mcps_restored), 1)
        self.assertFalse(mcps_restored[0].shelved)
        self.assertTrue(mcps_restored[0].enabled)

        # Verify it is back in settings.json
        s_data_restored = ag.read_json_file(ag.settings_file)
        self.assertIn("heavy-mcp", s_data_restored.get("mcpServers", {}))

        # 2. Test Claude Project-Scoped Shelving with sidecar
        cl = ClaudeConfigManager()
        fake_claude_json = os.path.join(self.tmp_dir, "claude_shelve_test.json")
        fake_claude_dir = os.path.join(self.tmp_dir, "fake_claude_shelve_dir")
        os.makedirs(fake_claude_dir, exist_ok=True)
        cl.claude_json_file = fake_claude_json
        cl.claude_dir = fake_claude_dir
        cl.settings_file = os.path.join(fake_claude_dir, "settings.json")

        proj_path = os.path.join(self.tmp_dir, "my_shelve_proj")
        os.makedirs(proj_path, exist_ok=True)
        proj_mcp = McpServer(
            name="proj-heavy-mcp",
            server_type="stdio",
            command="uvx",
            args=["proj-tool"],
            enabled=True,
            scope="project",
            project_path=proj_path
        )
        cl.save_mcp(proj_mcp)
        self.assertEqual(len(cl.list_mcps()), 1)

        # Shelve project mcp
        self.assertTrue(cl.shelve_mcp(proj_mcp))

        # Verify completely removed from claude.json
        c_data = cl.read_json_file(fake_claude_json)
        self.assertNotIn("proj-heavy-mcp", c_data.get("projects", {}).get(proj_path, {}).get("mcpServers", {}))
        self.assertNotIn("proj-heavy-mcp", c_data.get("mcpServers", {}))

        # Verify sidecar file exists next to claude.json
        self.assertTrue(os.path.exists(cl._get_shelved_path()))

        # Verify list_mcps shows it as shelved
        cl_mcps = cl.list_mcps()
        self.assertEqual(len(cl_mcps), 1)
        self.assertTrue(cl_mcps[0].shelved)
        self.assertEqual(cl_mcps[0].scope, "project")
        self.assertEqual(cl_mcps[0].project_path, proj_path)

        # Unshelve
        self.assertTrue(cl.unshelve_mcp(cl_mcps[0]))
        c_data_restored = cl.read_json_file(fake_claude_json)
        self.assertIn("proj-heavy-mcp", c_data_restored.get("projects", {}).get(proj_path, {}).get("mcpServers", {}))

        # 3. Test OpenCode Shelving
        oc = OpenCodeConfigManager()
        fake_opencode_dir = os.path.join(self.tmp_dir, "opencode_shelve_test")
        os.makedirs(fake_opencode_dir, exist_ok=True)
        oc.config_dir = fake_opencode_dir
        oc.jsonc_file = os.path.join(fake_opencode_dir, "opencode.jsonc")
        oc.json_file = os.path.join(fake_opencode_dir, "opencode.json")

        oc_mcp = McpServer(
            name="opencode-heavy",
            server_type="stdio",
            command="npx",
            args=["-y", "opencode-tool"],
            enabled=True
        )
        oc.save_mcp(oc_mcp)
        self.assertEqual(len(oc.list_mcps()), 1)

        # Shelve
        self.assertTrue(oc.shelve_mcp(oc_mcp))
        oc_data = oc.read_json_file(oc.jsonc_file)
        self.assertNotIn("opencode-heavy", oc_data.get("mcp", {}))
        
        oc_list = oc.list_mcps()
        self.assertEqual(len(oc_list), 1)
        self.assertTrue(oc_list[0].shelved)

        # Unshelve
        self.assertTrue(oc.unshelve_mcp(oc_list[0]))
        oc_data_restored = oc.read_json_file(oc.jsonc_file)
        self.assertIn("opencode-heavy", oc_data_restored.get("mcp", {}))

    def test_is_valid_project_path(self):
        home = os.path.expanduser("~")
        self.assertFalse(BaseConfigManager.is_valid_project_path(None))
        self.assertFalse(BaseConfigManager.is_valid_project_path(""))
        self.assertFalse(BaseConfigManager.is_valid_project_path("~"))
        self.assertFalse(BaseConfigManager.is_valid_project_path("/"))
        self.assertFalse(BaseConfigManager.is_valid_project_path(home))
        self.assertFalse(BaseConfigManager.is_valid_project_path(os.path.join(home, ".gemini")))
        self.assertFalse(BaseConfigManager.is_valid_project_path(os.path.join(home, ".gemini", "skills")))
        self.assertFalse(BaseConfigManager.is_valid_project_path(os.path.join(home, ".claude")))
        self.assertFalse(BaseConfigManager.is_valid_project_path(os.path.join(home, ".config", "some-app")))
        self.assertFalse(BaseConfigManager.is_valid_project_path(os.path.join(home, "non_existent_folder_xyz123")))

        # Valid project path
        valid_proj = os.path.join(self.tmp_dir, "my_cool_project")
        os.makedirs(valid_proj, exist_ok=True)
        self.assertTrue(BaseConfigManager.is_valid_project_path(valid_proj))

    def test_antigravity_does_not_duplicate_home_mcps_or_skills(self):
        fake_gemini_dir = os.path.join(self.tmp_dir, "gemini_home_dup_test")
        os.makedirs(os.path.join(fake_gemini_dir, "config"), exist_ok=True)
        ag = AntigravityConfigManager(base_dir=fake_gemini_dir)

        # 1. Global MCP in mcp_config.json
        ag.write_json_file(ag.mcp_config_file, {
            "mcpServers": {
                "github": {"type": "http", "url": "https://api.githubcopilot.com/mcp"}
            }
        })

        # 2. projects.json contains home directory and valid project
        home = os.path.expanduser("~")
        valid_proj = os.path.join(self.tmp_dir, "valid_proj")
        os.makedirs(os.path.join(valid_proj, ".gemini"), exist_ok=True)
        ag.write_json_file(os.path.join(valid_proj, ".gemini", "settings.json"), {
            "mcpServers": {
                "project-tool": {"type": "stdio", "command": "echo", "args": ["hi"]}
            }
        })

        ag.write_json_file(ag.projects_file, {
            "projects": {
                home: "user-home",
                os.path.join(home, ".gemini"): "gemini-dir",
                valid_proj: "valid-proj"
            }
        })

        mcps = ag.list_mcps()
        # Should have exactly 2 MCPs: 1 global github, 1 project-tool in valid_proj
        # NO project-scoped github for home!
        self.assertEqual(len(mcps), 2)
        github_mcps = [m for m in mcps if m.name == "github"]
        self.assertEqual(len(github_mcps), 1)
        self.assertEqual(github_mcps[0].scope, "global")

        proj_mcps = [m for m in mcps if m.scope == "project"]
        self.assertEqual(len(proj_mcps), 1)
        self.assertEqual(proj_mcps[0].name, "project-tool")
        self.assertEqual(proj_mcps[0].project_path, valid_proj)

    def test_claude_does_not_load_home_as_project_mcp(self):
        cl = ClaudeConfigManager()
        fake_claude_json = os.path.join(self.tmp_dir, "claude_home_test.json")
        fake_claude_dir = os.path.join(self.tmp_dir, "fake_claude_dir")
        os.makedirs(fake_claude_dir, exist_ok=True)
        cl.claude_json_file = fake_claude_json
        cl.claude_dir = fake_claude_dir
        cl.settings_file = os.path.join(fake_claude_dir, "settings.json")

        home = os.path.expanduser("~")
        cl.write_json_file(fake_claude_json, {
            "mcpServers": {
                "global-tool": {"type": "stdio", "command": "glab", "args": ["mcp"]}
            },
            "projects": {
                home: {
                    "_disabledMcpServers": {
                        "clickup": {"type": "http", "url": "https://mcp.clickup.com/mcp"}
                    }
                }
            }
        })

        mcps = cl.list_mcps()
        self.assertEqual(len(mcps), 1)
        self.assertEqual(mcps[0].name, "global-tool")
        self.assertEqual(mcps[0].scope, "global")

    def test_project_registration(self):
        target_proj = os.path.join(self.tmp_dir, "custom_registered_proj")
        os.makedirs(target_proj, exist_ok=True)
        
        self.assertTrue(BaseConfigManager.is_valid_project_path(target_proj))
        BaseConfigManager.register_known_project(target_proj)
        
        projects = BaseConfigManager.get_known_projects()
        self.assertIn(target_proj, projects)

    def test_windows_and_root_path_validation(self):
        # Reject root paths
        self.assertFalse(BaseConfigManager.is_valid_project_path("/"))
        self.assertFalse(BaseConfigManager.is_valid_project_path("~"))
        self.assertFalse(BaseConfigManager.is_valid_project_path(""))
        self.assertFalse(BaseConfigManager.is_valid_project_path(None))

        # Check drive root rejection
        drive, tail = os.path.splitdrive("C:\\")
        if drive:
            self.assertFalse(BaseConfigManager.is_valid_project_path("C:\\"))
            self.assertFalse(BaseConfigManager.is_valid_project_path("C:/"))

    def test_secure_file_permissions(self):
        target_file = os.path.join(self.tmp_dir, "secure_config.json")
        BaseConfigManager.write_json_file(target_file, {"token": "secret_123"})
        self.assertTrue(os.path.exists(target_file))
        if hasattr(os, 'stat') and os.name == 'posix':
            mode = oct(os.stat(target_file).st_mode & 0o777)
            self.assertEqual(mode, '0o600')

    def test_secret_masking(self):
        url = "postgresql://myuser:supersecretpass@localhost:5432/mydb"
        masked = McpServer.mask_secrets(url)
        self.assertNotIn("supersecretpass", masked)
        self.assertIn("••••••••", masked)

        url_with_token = "https://mcp.company.com/mcp?token=xyz123abc456"
        masked_token = McpServer.mask_secrets(url_with_token)
        self.assertNotIn("xyz123abc456", masked_token)
        self.assertIn("••••••••", masked_token)

    def test_backup_pruning(self):
        orig_backup_dir = BaseConfigManager.BACKUP_DIR
        test_bkp_dir = os.path.join(self.tmp_dir, "test_backups")
        BaseConfigManager.BACKUP_DIR = test_bkp_dir
        try:
            target_file = os.path.join(self.tmp_dir, "config_to_backup.json")
            BaseConfigManager.write_json_file(target_file, {"version": 1}, backup=False)

            # Create 15 backups
            for i in range(15):
                BaseConfigManager.write_json_file(target_file, {"version": i}, backup=True)

            # Check that count does not exceed MAX_BACKUPS_PER_FILE (10)
            backups = [f for f in os.listdir(test_bkp_dir) if f.endswith(".bak")]
            self.assertLessEqual(len(backups), BaseConfigManager.MAX_BACKUPS_PER_FILE)
        finally:
            BaseConfigManager.BACKUP_DIR = orig_backup_dir

if __name__ == '__main__':
    unittest.main()




