"""Small durable authority: atomic state, content-addressed artifacts and one-use ledger."""

from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest(value):
    return sha256(canonical(value)).hexdigest()


def atomic_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("wb", dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(canonical(value))
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def put_artifact(directory: Path, data: bytes, artifact_type: str, source: str):
    if not isinstance(data, bytes) or not artifact_type:
        raise ValueError("invalid artifact")
    identity = sha256(data).hexdigest()
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / identity
    if not path.exists():
        with tempfile.NamedTemporaryFile("wb", dir=directory, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    return {"sha256": identity, "type": artifact_type, "source": source}


def get_artifact(directory: Path, ref):
    identity = ref["sha256"]
    if len(identity) != 64 or any(c not in "0123456789abcdef" for c in identity):
        raise ValueError("invalid artifact identity")
    data = (directory / identity).read_bytes()
    if sha256(data).hexdigest() != identity:
        raise ValueError("artifact hash mismatch")
    return data


def consume_once(ledger: Path, grant, request_sha: str):
    ledger.mkdir(parents=True, exist_ok=True)
    key = sha256((grant.host_id + "\0" + grant.ingress_id).encode()).hexdigest()
    path = ledger / key
    value = {"host_id": grant.host_id, "ingress_id": grant.ingress_id,
             "session_id": grant.session_id, "request_sha256": request_sha,
             "receipt_sha256": grant.receipt_sha256, "mode": grant.mode}
    with path.open("xb") as stream:
        stream.write(canonical(value))
        stream.flush()
        os.fsync(stream.fileno())
