import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Independent Agent-Loop Core Host entry. No production Session starts by default.")
    parser.add_argument("--config", type=Path, required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("mcp", help="Serve local stdio MCP; issuance is outside MCP.")
    commands.add_parser("catalog", help="Read installed capabilities, candidate skills and bound templates.")
    commands.add_parser("smoke", help="Import/config/protocol construction only; zero production Session, model or Tool effects.")
    start = commands.add_parser("start")
    start.add_argument("grant_id")
    for name in ("advance", "status"):
        item = commands.add_parser(name)
        item.add_argument("session_id")
    deliver = commands.add_parser("deliver")
    deliver.add_argument("session_id")
    deliver.add_argument("output_directory")
    grant = commands.add_parser("issue-grant", help="Trusted Host only, after a direct User Session-start decision.")
    grant.add_argument("grant_id")
    grant.add_argument("session_id")
    grant.add_argument("--request", required=True)
    grant.add_argument("--reference", action="append", default=[])
    grant.add_argument("--user-evidence", required=True, type=Path)
    grant.add_argument("--host-confirmed-explicit-user-start", action="store_true")
    args = parser.parse_args()
    if args.command == "mcp":
        from .mcp_server import server
        server(args.config).run(transport="stdio")
        return
    from .runtime import Runtime
    runtime = Runtime(args.config)
    if args.command == "issue-grant":
        result = runtime.host.issue_grant(args.grant_id, args.session_id, args.request, args.reference,
            json.loads(args.user_evidence.read_text(encoding="utf-8")), start_authorized=args.host_confirmed_explicit_user_start)
    elif args.command in {"catalog", "smoke"}:
        runtime.bootstrap_knowledge()
        result = {"scope": "BOOTSTRAP_ONLY_NO_PRODUCTION_SESSION_NO_INFERENCE_NO_TOOL_EFFECT",
                  "capabilities": runtime.tools.capabilities(), "skills": [s["value"]["id"] for s in runtime.sessions.skills()]}
    elif args.command == "start":
        state = runtime.sessions.start(args.grant_id)
        result = runtime.status(state["id"])
    elif args.command in {"advance", "status"}:
        result = getattr(runtime, args.command)(args.session_id)
    elif args.command == "deliver":
        result = runtime.deliver(args.session_id, args.output_directory)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
