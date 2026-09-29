"""Codex CLI account-mode probe used by the generic Reviewer boundary."""

import subprocess
from pathlib import Path


def auth_mode(env):
    if any(env.get(k) for k in ("OPENAI_API_KEY", "CODEX_API_KEY", "CODEX_ACCESS_TOKEN", "OPENAI_FEDERATION_RULE_ID", "OPENAI_IDENTITY_TOKEN_FILE")):
        return "API_KEY"
    codex_home = env.get("CODEX_HOME") or str(Path("C:/Users/Worker/.codex"))
    probe_env = dict(env, CODEX_HOME=codex_home)
    status = subprocess.run(["codex", "login", "status"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20, env=probe_env)
    if status.returncode == 0 and "Logged in using ChatGPT" in (status.stdout + status.stderr):
        return "CHATGPT_ACCOUNT"
    return "UNKNOWN"
