"""MCP Resources adapter (stub for Phase 7).

This will expose domain data as MCP resources:
- run://<run_id>
- diff://<approval_id>
- trace://<run_id>
- artifact://<artifact_id>
"""

# TODO: Implement in Phase 7
#
# from mcp.server import Server
#
# def register_resources(server: Server, container: DIContainer) -> None:
#     @server.resource("run://{run_id}")
#     async def get_run(run_id: str) -> dict:
#         ...
#
#     @server.resource("diff://{approval_id}")
#     async def get_diff(approval_id: str) -> str:
#         ...
#
#     @server.resource("trace://{run_id}")
#     async def get_trace(run_id: str) -> list[dict]:
#         ...
