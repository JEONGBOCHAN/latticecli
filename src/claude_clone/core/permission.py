"""PermissionManager - Tool execution permission system

Manages permissions for tool execution with allow/deny rules.
Supports different modes: default, plan, accept_edits, bypass.

Usage:
    from claude_clone.core.permission import PermissionManager, PermissionResult

    manager = PermissionManager(mode="default", allow_rules=[], deny_rules=[])
    result = manager.check("Edit", {"file_path": "src/main.py"})
    if result == PermissionResult.ALLOW:
        # Execute tool
    elif result == PermissionResult.DENY:
        # Block execution
    else:  # PermissionResult.ASK
        # Prompt user for permission
"""

import fnmatch
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


class PermissionMode(str, Enum):
    """Permission mode determines default behavior"""

    DEFAULT = "default"  # Ask for dangerous operations
    PLAN = "plan"  # Read-only, ask for all writes
    ACCEPT_EDITS = "accept_edits"  # Auto-approve edits, ask for bash
    BYPASS = "bypass"  # Auto-approve everything (dangerous!)


class PermissionResult(str, Enum):
    """Result of permission check"""

    ALLOW = "allow"  # Automatically allowed
    DENY = "deny"  # Automatically denied
    ASK = "ask"  # Ask user for permission


@dataclass
class PermissionRule:
    """Parsed permission rule

    Rule format: "ToolName" or "ToolName(pattern)"
    Examples:
        - "Read" - matches all Read operations
        - "Bash(npm run:*)" - matches Bash with command starting with "npm run"
        - "Edit(src/**/*.py)" - matches Edit for Python files in src/
        - "Read(.env*)" - matches Read for .env files
    """

    tool_name: str
    pattern: str | None = None

    @classmethod
    def parse(cls, rule: str) -> "PermissionRule":
        """Parse a rule string into PermissionRule

        Args:
            rule: Rule string like "Read" or "Edit(src/**/*.py)"

        Returns:
            Parsed PermissionRule
        """
        # Match "ToolName(pattern)" or "ToolName"
        match = re.match(r"^(\w+)(?:\((.+)\))?$", rule.strip())
        if not match:
            return cls(tool_name=rule.strip(), pattern=None)

        tool_name = match.group(1)
        pattern = match.group(2)  # May be None

        return cls(tool_name=tool_name, pattern=pattern)

    def matches(self, tool_name: str, args: dict[str, Any]) -> bool:
        """Check if this rule matches a tool invocation

        Args:
            tool_name: Name of the tool being invoked
            args: Tool arguments

        Returns:
            True if rule matches
        """
        # Tool name must match
        if self.tool_name != tool_name:
            return False

        # If no pattern, match all invocations of this tool
        if self.pattern is None:
            return True

        # Get the relevant argument to match against
        match_value = self._get_match_value(tool_name, args)
        if match_value is None:
            return False

        # Match pattern against value
        return self._pattern_matches(self.pattern, match_value)

    def _get_match_value(self, tool_name: str, args: dict[str, Any]) -> str | None:
        """Get the value to match pattern against based on tool type"""
        # For file-related tools, match against file_path
        if tool_name in ("Read", "Edit", "Write", "read_tool", "edit_tool", "write_tool"):
            return args.get("file_path")

        # For Bash, match against command
        if tool_name in ("Bash", "bash_tool"):
            return args.get("command")

        # For Grep, match against pattern or path
        if tool_name in ("Grep", "grep_tool"):
            return args.get("path") or args.get("pattern")

        # For Glob, match against pattern or path
        if tool_name in ("Glob", "glob_tool"):
            return args.get("path") or args.get("pattern")

        # Default: try common argument names
        return args.get("file_path") or args.get("path") or args.get("command")

    def _pattern_matches(self, pattern: str, value: str) -> bool:
        """Check if pattern matches value

        Supports:
        - Glob patterns: *.py, src/**/*.ts
        - Prefix patterns: npm run:* -> matches "npm run test"
        - Exact match
        """
        # Handle prefix pattern with colon (e.g., "npm run:*")
        if ":*" in pattern:
            prefix = pattern.replace(":*", "")
            return value.startswith(prefix)

        # Handle ** glob pattern (recursive directory matching)
        if "**" in pattern:
            # Convert ** glob pattern to regex
            # ** matches zero or more path segments including /
            # Use placeholders to avoid conflicts during replacement
            DOUBLE_STAR_SLASH = "\x00DS\x00"
            DOUBLE_STAR = "\x01DS\x01"
            SINGLE_STAR = "\x02SS\x02"

            regex_pattern = pattern
            # Replace **/ first (zero or more directories)
            regex_pattern = regex_pattern.replace("**/", DOUBLE_STAR_SLASH)
            # Replace remaining ** (matches anything)
            regex_pattern = regex_pattern.replace("**", DOUBLE_STAR)
            # Replace single *
            regex_pattern = regex_pattern.replace("*", SINGLE_STAR)
            # Escape dots
            regex_pattern = regex_pattern.replace(".", r"\.")
            # Now replace placeholders with actual regex
            regex_pattern = regex_pattern.replace(DOUBLE_STAR_SLASH, "(?:.*/)?")
            regex_pattern = regex_pattern.replace(DOUBLE_STAR, ".*")
            regex_pattern = regex_pattern.replace(SINGLE_STAR, "[^/]*")
            regex_pattern = f"^{regex_pattern}$"
            return bool(re.match(regex_pattern, value))

        # Use fnmatch for simple glob patterns
        return fnmatch.fnmatch(value, pattern)


class PermissionManager:
    """Manages tool execution permissions

    Attributes:
        mode: Permission mode (default, plan, accept_edits, bypass)
        allow_rules: List of allow rules
        deny_rules: List of deny rules
    """

    # Tools considered safe (read-only)
    SAFE_TOOLS = {"Read", "read_tool", "Glob", "glob_tool", "Grep", "grep_tool"}

    # Tools that modify files
    WRITE_TOOLS = {"Edit", "edit_tool", "Write", "write_tool"}

    # Tools that execute commands
    EXEC_TOOLS = {"Bash", "bash_tool"}

    def __init__(
        self,
        mode: str | PermissionMode = PermissionMode.DEFAULT,
        allow_rules: list[str] | None = None,
        deny_rules: list[str] | None = None,
    ):
        """Initialize PermissionManager

        Args:
            mode: Permission mode
            allow_rules: List of allow rule strings
            deny_rules: List of deny rule strings
        """
        if isinstance(mode, str):
            try:
                self.mode = PermissionMode(mode)
            except ValueError:
                self.mode = PermissionMode.DEFAULT
        else:
            self.mode = mode

        self._allow_rules = [
            PermissionRule.parse(r) for r in (allow_rules or [])
        ]
        self._deny_rules = [
            PermissionRule.parse(r) for r in (deny_rules or [])
        ]

    def check(self, tool_name: str, args: dict[str, Any] | None = None) -> PermissionResult:
        """Check if tool execution is permitted

        Args:
            tool_name: Name of the tool to execute
            args: Tool arguments

        Returns:
            PermissionResult indicating whether to allow, deny, or ask
        """
        args = args or {}

        # 1. Check deny rules first (deny always wins)
        for rule in self._deny_rules:
            if rule.matches(tool_name, args):
                return PermissionResult.DENY

        # 2. Check allow rules
        for rule in self._allow_rules:
            if rule.matches(tool_name, args):
                return PermissionResult.ALLOW

        # 3. Apply mode-based defaults
        return self._check_by_mode(tool_name)

    def _check_by_mode(self, tool_name: str) -> PermissionResult:
        """Apply mode-based permission defaults"""
        if self.mode == PermissionMode.BYPASS:
            # Bypass mode: allow everything
            return PermissionResult.ALLOW

        if self.mode == PermissionMode.PLAN:
            # Plan mode: allow read-only, ask for everything else
            if tool_name in self.SAFE_TOOLS:
                return PermissionResult.ALLOW
            return PermissionResult.ASK

        if self.mode == PermissionMode.ACCEPT_EDITS:
            # Accept edits mode: allow safe + write, ask for exec
            if tool_name in self.SAFE_TOOLS or tool_name in self.WRITE_TOOLS:
                return PermissionResult.ALLOW
            return PermissionResult.ASK

        # Default mode: allow safe tools, ask for others
        if tool_name in self.SAFE_TOOLS:
            return PermissionResult.ALLOW
        return PermissionResult.ASK

    def is_safe_tool(self, tool_name: str) -> bool:
        """Check if a tool is considered safe (read-only)"""
        return tool_name in self.SAFE_TOOLS

    def is_write_tool(self, tool_name: str) -> bool:
        """Check if a tool modifies files"""
        return tool_name in self.WRITE_TOOLS

    def is_exec_tool(self, tool_name: str) -> bool:
        """Check if a tool executes commands"""
        return tool_name in self.EXEC_TOOLS

    def format_permission_prompt(
        self,
        tool_name: str,
        args: dict[str, Any] | None = None,
    ) -> str:
        """Format a permission prompt message for the user

        Args:
            tool_name: Name of the tool
            args: Tool arguments

        Returns:
            Formatted prompt string
        """
        args = args or {}

        if tool_name in ("Edit", "edit_tool"):
            file_path = args.get("file_path", "unknown")
            return f"Allow editing {file_path}?"

        if tool_name in ("Write", "write_tool"):
            file_path = args.get("file_path", "unknown")
            return f"Allow writing to {file_path}?"

        if tool_name in ("Bash", "bash_tool"):
            command = args.get("command", "unknown")
            # Truncate long commands
            if len(command) > 50:
                command = command[:47] + "..."
            return f"Allow running: {command}?"

        if tool_name in ("Read", "read_tool"):
            file_path = args.get("file_path", "unknown")
            return f"Allow reading {file_path}?"

        return f"Allow {tool_name}?"


def create_permission_manager_from_config(
    permission_mode: str = "default",
    allow_rules: list[str] | None = None,
    deny_rules: list[str] | None = None,
) -> PermissionManager:
    """Create PermissionManager from config values

    Args:
        permission_mode: Permission mode string
        allow_rules: Allow rules from config
        deny_rules: Deny rules from config

    Returns:
        Configured PermissionManager
    """
    return PermissionManager(
        mode=permission_mode,
        allow_rules=allow_rules,
        deny_rules=deny_rules,
    )
