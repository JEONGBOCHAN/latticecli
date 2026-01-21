"""Infrastructure layer - Frameworks and drivers.

This is the outermost layer. It knows about all other layers
and is responsible for wiring everything together.
"""

from claude_clone.infrastructure.container import DIContainer

__all__ = ["DIContainer"]
