"""Claude Clone - CLI-based AI Coding Assistant

Entry point module for the application.

Usage:
    # Via console script (after installation)
    $ claude-clone

    # Via Python module
    $ python -m claude_clone
"""

from claude_clone.cli.app import run


def main() -> None:
    """CLI entry point

    This function is called by the console script defined in pyproject.toml:
        [project.scripts]
        claude-clone = "claude_clone.main:main"
    """
    run()


if __name__ == "__main__":
    main()
