"""Tests for PermissionManager"""

import pytest

from claude_clone.core.permission import (
    create_permission_manager_from_config,
    PermissionManager,
    PermissionMode,
    PermissionResult,
    PermissionRule,
)


class TestPermissionRule:
    """Tests for PermissionRule parsing and matching"""

    def test_parse_simple_rule(self) -> None:
        """Test parsing a simple tool name rule"""
        rule = PermissionRule.parse("Read")

        assert rule.tool_name == "Read"
        assert rule.pattern is None

    def test_parse_rule_with_pattern(self) -> None:
        """Test parsing a rule with pattern"""
        rule = PermissionRule.parse("Edit(src/**/*.py)")

        assert rule.tool_name == "Edit"
        assert rule.pattern == "src/**/*.py"

    def test_parse_rule_with_prefix_pattern(self) -> None:
        """Test parsing a rule with prefix pattern"""
        rule = PermissionRule.parse("Bash(npm run:*)")

        assert rule.tool_name == "Bash"
        assert rule.pattern == "npm run:*"

    def test_matches_simple_rule(self) -> None:
        """Test matching a simple rule"""
        rule = PermissionRule.parse("Read")

        assert rule.matches("Read", {"file_path": "/any/file.py"})
        assert not rule.matches("Edit", {"file_path": "/any/file.py"})

    def test_matches_glob_pattern(self) -> None:
        """Test matching a glob pattern"""
        rule = PermissionRule.parse("Edit(src/**/*.py)")

        assert rule.matches("Edit", {"file_path": "src/main.py"})
        assert rule.matches("Edit", {"file_path": "src/utils/helper.py"})
        assert not rule.matches("Edit", {"file_path": "tests/test_main.py"})
        assert not rule.matches("Edit", {"file_path": "src/main.js"})

    def test_matches_prefix_pattern(self) -> None:
        """Test matching a prefix pattern"""
        rule = PermissionRule.parse("Bash(npm run:*)")

        assert rule.matches("Bash", {"command": "npm run test"})
        assert rule.matches("Bash", {"command": "npm run build"})
        assert not rule.matches("Bash", {"command": "npm install"})
        assert not rule.matches("Bash", {"command": "yarn run test"})

    def test_matches_exact_pattern(self) -> None:
        """Test matching exact pattern"""
        rule = PermissionRule.parse("Bash(git status)")

        assert rule.matches("Bash", {"command": "git status"})
        assert not rule.matches("Bash", {"command": "git status -s"})

    def test_matches_wildcard_pattern(self) -> None:
        """Test matching wildcard pattern"""
        rule = PermissionRule.parse("Read(.env*)")

        assert rule.matches("Read", {"file_path": ".env"})
        assert rule.matches("Read", {"file_path": ".env.local"})
        assert rule.matches("Read", {"file_path": ".env.production"})
        assert not rule.matches("Read", {"file_path": "config.env"})


class TestPermissionManager:
    """Tests for PermissionManager"""

    def test_default_mode_allows_safe_tools(self) -> None:
        """Test that default mode allows safe tools"""
        manager = PermissionManager(mode=PermissionMode.DEFAULT)

        assert manager.check("Read") == PermissionResult.ALLOW
        assert manager.check("Glob") == PermissionResult.ALLOW
        assert manager.check("Grep") == PermissionResult.ALLOW
        assert manager.check("read_tool") == PermissionResult.ALLOW

    def test_default_mode_asks_for_write_tools(self) -> None:
        """Test that default mode asks for write tools"""
        manager = PermissionManager(mode=PermissionMode.DEFAULT)

        assert manager.check("Edit") == PermissionResult.ASK
        assert manager.check("Write") == PermissionResult.ASK
        assert manager.check("edit_tool") == PermissionResult.ASK

    def test_default_mode_asks_for_exec_tools(self) -> None:
        """Test that default mode asks for exec tools"""
        manager = PermissionManager(mode=PermissionMode.DEFAULT)

        assert manager.check("Bash") == PermissionResult.ASK
        assert manager.check("bash_tool") == PermissionResult.ASK

    def test_bypass_mode_allows_everything(self) -> None:
        """Test that bypass mode allows everything"""
        manager = PermissionManager(mode=PermissionMode.BYPASS)

        assert manager.check("Read") == PermissionResult.ALLOW
        assert manager.check("Edit") == PermissionResult.ALLOW
        assert manager.check("Bash") == PermissionResult.ALLOW

    def test_plan_mode_allows_safe_asks_others(self) -> None:
        """Test that plan mode allows safe tools, asks for others"""
        manager = PermissionManager(mode=PermissionMode.PLAN)

        assert manager.check("Read") == PermissionResult.ALLOW
        assert manager.check("Glob") == PermissionResult.ALLOW
        assert manager.check("Edit") == PermissionResult.ASK
        assert manager.check("Bash") == PermissionResult.ASK

    def test_accept_edits_mode_allows_writes(self) -> None:
        """Test that accept_edits mode allows writes, asks for exec"""
        manager = PermissionManager(mode=PermissionMode.ACCEPT_EDITS)

        assert manager.check("Read") == PermissionResult.ALLOW
        assert manager.check("Edit") == PermissionResult.ALLOW
        assert manager.check("Write") == PermissionResult.ALLOW
        assert manager.check("Bash") == PermissionResult.ASK

    def test_deny_rules_override_mode(self) -> None:
        """Test that deny rules override mode defaults"""
        manager = PermissionManager(
            mode=PermissionMode.BYPASS,
            deny_rules=["Read(.env*)"],
        )

        assert manager.check("Read", {"file_path": ".env"}) == PermissionResult.DENY
        assert manager.check("Read", {"file_path": "main.py"}) == PermissionResult.ALLOW

    def test_allow_rules_override_mode(self) -> None:
        """Test that allow rules override mode defaults"""
        manager = PermissionManager(
            mode=PermissionMode.DEFAULT,
            allow_rules=["Edit(src/**/*.py)"],
        )

        assert manager.check("Edit", {"file_path": "src/main.py"}) == PermissionResult.ALLOW
        assert manager.check("Edit", {"file_path": "tests/test.py"}) == PermissionResult.ASK

    def test_deny_takes_precedence_over_allow(self) -> None:
        """Test that deny rules take precedence over allow rules"""
        manager = PermissionManager(
            mode=PermissionMode.DEFAULT,
            allow_rules=["Read"],
            deny_rules=["Read(.env*)"],
        )

        assert manager.check("Read", {"file_path": "main.py"}) == PermissionResult.ALLOW
        assert manager.check("Read", {"file_path": ".env"}) == PermissionResult.DENY

    def test_multiple_allow_rules(self) -> None:
        """Test multiple allow rules"""
        manager = PermissionManager(
            mode=PermissionMode.DEFAULT,
            allow_rules=[
                "Bash(npm run:*)",
                "Bash(git status)",
                "Edit(src/**/*.py)",
            ],
        )

        assert manager.check("Bash", {"command": "npm run test"}) == PermissionResult.ALLOW
        assert manager.check("Bash", {"command": "git status"}) == PermissionResult.ALLOW
        assert manager.check("Bash", {"command": "rm -rf /"}) == PermissionResult.ASK
        assert manager.check("Edit", {"file_path": "src/main.py"}) == PermissionResult.ALLOW

    def test_multiple_deny_rules(self) -> None:
        """Test multiple deny rules"""
        manager = PermissionManager(
            mode=PermissionMode.BYPASS,
            deny_rules=[
                "Read(.env*)",
                "Bash(rm -rf:*)",
                "Edit(*.exe)",
            ],
        )

        assert manager.check("Read", {"file_path": ".env"}) == PermissionResult.DENY
        assert manager.check("Bash", {"command": "rm -rf /"}) == PermissionResult.DENY
        assert manager.check("Edit", {"file_path": "virus.exe"}) == PermissionResult.DENY
        assert manager.check("Read", {"file_path": "main.py"}) == PermissionResult.ALLOW

    def test_mode_string_conversion(self) -> None:
        """Test that mode can be specified as string"""
        manager = PermissionManager(mode="bypass")
        assert manager.mode == PermissionMode.BYPASS

        manager = PermissionManager(mode="default")
        assert manager.mode == PermissionMode.DEFAULT

    def test_invalid_mode_defaults_to_default(self) -> None:
        """Test that invalid mode falls back to default"""
        manager = PermissionManager(mode="invalid_mode")
        assert manager.mode == PermissionMode.DEFAULT


class TestPermissionManagerHelpers:
    """Tests for PermissionManager helper methods"""

    def test_is_safe_tool(self) -> None:
        """Test is_safe_tool method"""
        manager = PermissionManager()

        assert manager.is_safe_tool("Read")
        assert manager.is_safe_tool("read_tool")
        assert manager.is_safe_tool("Glob")
        assert manager.is_safe_tool("Grep")
        assert not manager.is_safe_tool("Edit")
        assert not manager.is_safe_tool("Bash")

    def test_is_write_tool(self) -> None:
        """Test is_write_tool method"""
        manager = PermissionManager()

        assert manager.is_write_tool("Edit")
        assert manager.is_write_tool("edit_tool")
        assert manager.is_write_tool("Write")
        assert not manager.is_write_tool("Read")
        assert not manager.is_write_tool("Bash")

    def test_is_exec_tool(self) -> None:
        """Test is_exec_tool method"""
        manager = PermissionManager()

        assert manager.is_exec_tool("Bash")
        assert manager.is_exec_tool("bash_tool")
        assert not manager.is_exec_tool("Read")
        assert not manager.is_exec_tool("Edit")

    def test_format_permission_prompt_edit(self) -> None:
        """Test format_permission_prompt for Edit"""
        manager = PermissionManager()

        prompt = manager.format_permission_prompt("Edit", {"file_path": "src/main.py"})
        assert "editing" in prompt.lower()
        assert "src/main.py" in prompt

    def test_format_permission_prompt_bash(self) -> None:
        """Test format_permission_prompt for Bash"""
        manager = PermissionManager()

        prompt = manager.format_permission_prompt("Bash", {"command": "npm test"})
        assert "running" in prompt.lower()
        assert "npm test" in prompt

    def test_format_permission_prompt_truncates_long_command(self) -> None:
        """Test that long commands are truncated in prompt"""
        manager = PermissionManager()

        long_command = "x" * 100
        prompt = manager.format_permission_prompt("Bash", {"command": long_command})
        assert "..." in prompt
        assert len(prompt) < 100


class TestCreatePermissionManagerFromConfig:
    """Tests for create_permission_manager_from_config"""

    def test_create_with_defaults(self) -> None:
        """Test creating manager with defaults"""
        manager = create_permission_manager_from_config()

        assert manager.mode == PermissionMode.DEFAULT
        assert manager.check("Read") == PermissionResult.ALLOW

    def test_create_with_mode(self) -> None:
        """Test creating manager with mode"""
        manager = create_permission_manager_from_config(permission_mode="bypass")

        assert manager.mode == PermissionMode.BYPASS

    def test_create_with_rules(self) -> None:
        """Test creating manager with rules"""
        manager = create_permission_manager_from_config(
            permission_mode="default",
            allow_rules=["Edit(src/**/*.py)"],
            deny_rules=["Read(.env*)"],
        )

        assert manager.check("Edit", {"file_path": "src/main.py"}) == PermissionResult.ALLOW
        assert manager.check("Read", {"file_path": ".env"}) == PermissionResult.DENY
