"""Deterministic demonstration; no live model/tool calls."""

from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
import tempfile

from agent_loop import SessionEngine, SandboxHost, VerifiedStartGrant
from tests.test_loop import Frontier, Reviewer, Worker, skills, workflow


def main():
    with tempfile.TemporaryDirectory() as scratch:
        root = Path(scratch)
        host = SandboxHost(root, {"workspace_read", "workspace_write", "local_execute"})
        frontier = Frontier(workflow())
        engine = SessionEngine(root / "sessions", root / "ledger", host, frontier, Reviewer(),
                               {"make_middle": Worker(b"-views"),
                                "make_output": Worker(b"-mesh", fail_first=True)}, skills())
        request = "Create a mesh"
        grant = VerifiedStartGrant("demo-host", "explicit-user-event-1", "demo-1",
                                   sha256(request.encode()).hexdigest(),
                                   (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
                                   "runtime-receipt", "SYNTHETIC")
        engine.start(grant, request, b"image", "image", {"ready": True, "goal_kind": "mesh"},
                     {"max_attempts": 4, "max_reviews": 4, "max_frontier_calls": 5})
        accepted = engine.run("demo-1")
        result = engine.deliver("demo-1", accepted["checkpoints"][-1]["artifact"]["sha256"],
                                "synthetic-host-presentation")
        print({"status": result["status"], "run": result["run"], "usage": result["usage"],
               "checkpoints": [entry["stage"] for entry in result["checkpoints"]]})


if __name__ == "__main__":
    main()
