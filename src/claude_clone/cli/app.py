"""CLI Application - Typer-based command line interface

Provides the main CLI entry point for Claude Clone.
Supports both interactive REPL mode and one-shot command execution.

Usage:
    # Interactive mode (REPL)
    $ claude-clone

    # One-shot mode with prompt
    $ claude-clone "read main.py"

    # Specify model
    $ claude-clone --model gemini-2.0-flash
"""

from typing import Annotated, Optional

import typer

from claude_clone.backends import SimpleConfigLoader
from claude_clone.repl import run_repl, run_single_turn

# Create Typer app
app = typer.Typer(
    name="claude-clone",
    help="AI Coding Assistant - Claude Code Clone",
    add_completion=False,
    no_args_is_help=False,
)


@app.command()
def main(
    prompt: Annotated[
        Optional[str],
        typer.Argument(
            help="Optional prompt for one-shot mode. If not provided, starts interactive REPL.",
        ),
    ] = None,
    model: Annotated[
        Optional[str],
        typer.Option(
            "--model",
            "-m",
            help="Model to use (e.g., gemini-2.0-flash, gemini-1.5-pro)",
        ),
    ] = None,
    resume: Annotated[
        bool,
        typer.Option(
            "--resume",
            "-r",
            help="Resume previous session (not yet implemented)",
        ),
    ] = False,
) -> None:
    """Claude Clone - AI Coding Assistant

    Run without arguments for interactive mode, or provide a prompt for one-shot execution.

    Examples:
        claude-clone                     # Start interactive REPL
        claude-clone "read main.py"      # One-shot mode
        claude-clone -m gemini-1.5-pro   # Use specific model
    """
    # Load configuration
    config_loader = SimpleConfigLoader()
    config = config_loader.load()

    # Override model if specified
    if model:
        config = config.model_copy(update={"model": model})

    # Handle resume flag (placeholder for Phase 5)
    if resume:
        typer.echo("Session resume not yet implemented. Starting new session.")

    # Run in appropriate mode
    if prompt:
        # One-shot mode: execute single prompt and exit
        try:
            response = run_single_turn(config, prompt)
            if response:
                typer.echo(response)
        except Exception as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(code=1)
    else:
        # Interactive mode: start REPL
        try:
            run_repl(config)
        except KeyboardInterrupt:
            pass  # Clean exit on Ctrl+C
        except Exception as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(code=1)


def run() -> None:
    """Entry point for the CLI application

    This function is called by the console script defined in pyproject.toml.
    """
    app()
