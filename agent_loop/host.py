"""Host-owned ingress and capability boundary. No Core code reads a transcript."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class VerifiedStartGrant:
    host_id: str
    ingress_id: str
    session_id: str
    request_sha256: str
    expires_at: str
    receipt_sha256: str
    mode: str = "ACTUAL"


@dataclass(frozen=True)
class CapabilityRequest:
    capability: str
    effects: tuple[str, ...]
    paths: tuple[str, ...] = ()


class SandboxHost:
    """Policy check only; the Host must enforce its OS/process sandbox as well."""

    def __init__(self, root: Path, allowed_effects: set[str]):
        self.root = Path(root).resolve()
        self.allowed_effects = frozenset(allowed_effects)

    def authorize(self, request: CapabilityRequest) -> bool:
        if not request.capability or not set(request.effects) <= self.allowed_effects:
            return False
        return all(Path(path).resolve().is_relative_to(self.root) for path in request.paths)


class CodexTranscriptHost(SandboxHost):
    """Example Codex ingress verifier; fail closed on unknown transcript shapes.

    The caller supplies a runtime-owned JSONL path and exact line number. The host
    must additionally control the root and receipt/ledger outside the Core. This
    adapter is only usable where those runtime-owned transcript files are present.
    """

    def __init__(self, root: Path, allowed_effects: set[str], transcript_root: Path):
        super().__init__(root, allowed_effects)
        self.transcript_root = Path(transcript_root).resolve()

    def verify_start(self, transcript: Path, line_number: int, request: str,
                     session_id: str, expires_at: str,
                     explicit_start: Callable[[str], bool]) -> VerifiedStartGrant:
        path = Path(transcript).resolve()
        if not path.is_relative_to(self.transcript_root) or path.suffix != ".jsonl" or line_number < 1:
            raise ValueError("untrusted transcript location")
        with path.open("rb") as stream:
            first = stream.readline()
            meta = json.loads(first)
            thread_id = meta.get("payload", {}).get("id")
            if (meta.get("type") != "session_meta" or not isinstance(thread_id, str) or
                not thread_id or thread_id not in path.stem):
                raise ValueError("unbound Codex session transcript")
            stream.seek(0)
            for position, line in enumerate(stream, 1):
                if position == line_number:
                    break
            else:
                raise ValueError("missing transcript event")
        event = json.loads(line)
        payload = event.get("payload", {})
        if event.get("type") != "response_item" or payload.get("type") != "message" or payload.get("role") != "user":
            raise ValueError("not a User message event")
        content = payload.get("content", [])
        texts = [item.get("text") for item in content if item.get("type") == "input_text"]
        if len(texts) != 1 or texts[0] != request or not explicit_start(request):
            raise ValueError("no exact explicit User start")
        if not datetime.now(timezone.utc) < datetime.fromisoformat(expires_at) <= datetime.now(timezone.utc) + timedelta(hours=1):
            raise ValueError("expired ingress")
        digest = sha256(line).hexdigest()
        return VerifiedStartGrant("codex", f"{path.name}:{line_number}:{digest}",
                                  session_id, sha256(request.encode()).hexdigest(),
                                  expires_at, digest)
