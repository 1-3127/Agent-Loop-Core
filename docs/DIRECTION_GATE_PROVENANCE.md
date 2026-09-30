# Direction Gate v1 provenance

- Canonical document: Agent-Loop Direction Gate v1 — Codex Handoff
- Version: v1
- Original path: `C:\Users\Worker\.codex\attachments\9eb20a17-24a4-46f1-b47e-77f9345f809f\붙여넣은 텍스트.txt`
- Original SHA-256: `1b43f3ddad27f6da003530c2d83db34eee53289cacfa403524b375b6a2623862`
- Original size: 19242 bytes
- Repository path: `docs/Agent-Loop_Direction_Gate_v1.md`
- Repository SHA-256: `1b43f3ddad27f6da003530c2d83db34eee53289cacfa403524b375b6a2623862`
- Repository size: 19242 bytes
- Copied verbatim: true (Git text normalization disabled for this file)
- Scope authority only; no new requirements added.

## M7 scope decisions

F07 = KNOWN NON-BLOCKING LIMITATION / HARDENING. Sections 4, 5, and 10 require bounded execution, explicit terminals, and a C4 bounded run proof. Section 6 excludes comprehensive restart/resume, every crash-point recovery, and Reviewer reservation recovery. The Gate does not explicitly require terminalization of every infrastructure failure path as a Core v1 freeze criterion. Arbitrary failure/uncertain lifecycle terminalization is not claimed; uncertain submission is not automatically retried; production-grade recovery is not claimed.

F05 = NON-BLOCKING ARCHITECTURAL DEBT. Section 10 C5 requires minimal adapter swap smoke, including a deterministic/fake Worker if appropriate. A generic C1-C4 WorkerPort orchestration migration is not required.
