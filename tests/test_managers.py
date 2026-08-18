import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_managers import AntigravityConfigManager, ClaudeConfigManager, OpenCodeConfigManager
from models import McpServer, PluginSkill

class TestConfigManagers(unittest.TestCase):
    def test_antigravity_list(self):
        mgr = AntigravityConfigManager()
        mcps = mgr.list_mcps()
        print(f'Antigravity MCPs found: {len(mcps)}')
        for m in mcps:
            print(f'  - {m.name} ({m.display_type}, Enabled={m.enabled}): {m.command_display}')
        
        plugins = mgr.list_plugins_and_skills()
        print(f'Antigravity Plugins/Skills found: {len(plugins)}')
        for p in plugins[:5]:
            print(f'  - [{p.display_kind}] {p.name} (Enabled={p.enabled}): {p.description}')
        self.assertIsInstance(mcps, list)
        self.assertIsInstance(plugins, list)

    def test_claude_list(self):
        mgr = ClaudeConfigManager()
        mcps = mgr.list_mcps()
        print(f'Claude MCPs found: {len(mcps)}')
        for m in mcps:
            print(f'  - {m.name} ({m.display_type}, Enabled={m.enabled}): {m.command_display}')
        
        plugins = mgr.list_plugins_and_skills()
        print(f'Claude Plugins/Skills found: {len(plugins)}')
        for p in plugins[:5]:
            print(f'  - [{p.display_kind}] {p.name} (Enabled={p.enabled}): {p.source}')
        self.assertIsInstance(mcps, list)
        self.assertIsInstance(plugins, list)

    def test_opencode_list(self):
        mgr = OpenCodeConfigManager()
        mcps = mgr.list_mcps()
        print(f'OpenCode MCPs found: {len(mcps)}')
        for m in mcps:
            print(f'  - {m.name} ({m.display_type}, Enabled={m.enabled}): {m.command_display}')
        
        plugins = mgr.list_plugins_and_skills()
        print(f'OpenCode Plugins/Skills found: {len(plugins)}')
        for p in plugins[:5]:
            print(f'  - [{p.display_kind}] {p.name} (Enabled={p.enabled}): {p.source}')
        self.assertIsInstance(mcps, list)
        self.assertIsInstance(plugins, list)

if __name__ == '__main__':
    unittest.main()
