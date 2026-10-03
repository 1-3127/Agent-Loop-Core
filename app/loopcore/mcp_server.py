"""Local MCP transport; no grant-issuance tool is exposed."""
from mcp.server import MCPServer

from .runtime import Runtime


def server(config_path):
    runtime = Runtime(config_path)
    runtime.bootstrap_knowledge()
    mcp = MCPServer("Agent-Loop-Core", instructions="Host calls the bounded loop. User is outside its internal Session. "
        "New ACTUAL Sessions require a separately issued, verified User-origin grant. Terminal Sessions cannot execute again.")

    @mcp.tool()
    def loop_start(grant_id: str) -> dict:
        """Consume one existing Host-issued grant and start dialogue. Does not issue permission."""
        state = runtime.sessions.start(grant_id)
        return runtime.status(state["id"])

    @mcp.tool()
    def loop_advance(session_id: str) -> dict:
        """One Frontier decision and selected subordinate action within the frozen budget."""
        return runtime.advance(session_id)

    @mcp.tool()
    def loop_status(session_id: str) -> dict:
        """Read status, unresolved effects and required undelivered-artifact notice."""
        return runtime.status(session_id)

    @mcp.tool()
    def loop_clarify(session_id: str, host_receipt_id: str) -> dict:
        """Bind a verified User response to an unfinished dialogue, never reopen a terminal Session."""
        return runtime.clarify(session_id, host_receipt_id)

    @mcp.tool()
    def loop_recover(session_id: str, host_receipt_id: str) -> dict:
        """Apply a trusted Host recovery receipt. Observe original effects, never redispatch them."""
        return runtime.recover(session_id, host_receipt_id)

    @mcp.tool()
    def loop_deliver(session_id: str, output_directory: str) -> dict:
        """Export original inputs + internally accepted output to a Host-authorized fresh directory."""
        return runtime.deliver(session_id, output_directory)

    @mcp.tool()
    def loop_retention(session_id: str, reason: str, prune_artifact_ids: list[str], apply: bool = False) -> dict:
        """At Session end, record conservative Core/Frontier cleanup; optional recoverable quarantine."""
        return runtime.retention(session_id, {"reason": reason, "prune": prune_artifact_ids}, apply)

    return mcp
