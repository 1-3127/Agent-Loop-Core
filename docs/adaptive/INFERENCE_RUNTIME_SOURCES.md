# Inference runtime sources

Official OpenAI documentation was fetched before selecting the Codex CLI execution contract. Local installed `codex exec --help` confirmed the used flags.

- [Non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode): structured final responses through --output-schema and JSONL invocation events through --json.
- [Developer commands](https://learn.chatgpt.com/docs/developer-commands?surface=cli): --ephemeral, read-only sandbox, stdin prompt, images and workspace flags.
- [Agent Skills specification](https://agentskills.io/specification): portable SKILL.md frontmatter naming/description structure. No external Skill/script copied or executed for M1/M2.

These references establish CLI/portable-format behavior, not live account/model availability or actual production success. Saved auth remains inside Codex; no credential file is exported or logged.
