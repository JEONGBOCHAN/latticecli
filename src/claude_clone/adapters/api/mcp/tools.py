"""MCP Tools adapter (stub for Phase 7).

This will expose domain operations as MCP tools:
- runs_list
- runs_get
- approvals_list
- approvals_resolve
- artifacts_open
"""

# TODO: Implement in Phase 7
#
# from mcp.server import Server
# from claude_clone.application.use_cases import (
#     CreateRunUseCase,
#     ResolveApprovalUseCase,
#     GetTimelineUseCase,
# )
#
# def register_tools(server: Server, container: DIContainer) -> None:
#     @server.tool()
#     async def runs_list(limit: int = 10) -> list[dict]:
#         ...
#
#     @server.tool()
#     async def approvals_resolve(
#         approval_id: str,
#         approved: bool,
#         comment: str = ""
#     ) -> dict:
#         ...
