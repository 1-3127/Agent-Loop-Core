"""Authority, lifecycle and lineage in one transactional Session store.

No model, Host, network or domain execution code belongs in this module.
"""
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import time
import uuid


TERMINAL = {"CLOSED", "FAILED", "ABORT", "BLOCKED_SPECIFICATION_AMBIGUITY", "DELIVERY_FAILED"}
DURABILITY = {"TRANSIENT", "CHECKPOINT", "AUTHORITY", "OUTPUT"}


class ContractError(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise ContractError(reason)


def identity(value):
    require(isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,80}", value), "INVALID_ID")
    return value


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def strategy_hash(workflow):
    stages = deepcopy(workflow["stages"])
    for stage in stages:
        for pointer in stage["local_parameters"]:
            parts = pointer.strip("/").split("/")
            target = stage["parameters"]
            for key in parts[:-1]:
                target = target.get(key, {})
            target.pop(parts[-1], None)
    return digest(stages)


def file_ref(path):
    path = Path(path).resolve(strict=True)
    require(path.is_file(), "NOT_A_FILE")
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(block)
    return {"path": str(path), "sha256": sha.hexdigest(), "bytes": path.stat().st_size}


def check_ref(ref):
    require(isinstance(ref, dict) and file_ref(ref["path"]) == ref, "FILE_IDENTITY_CHANGED")
    return Path(ref["path"])


def write_once(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(canonical(value) + "\n")
    return file_ref(path)


class Sessions:
    def __init__(self, root, verify_grant):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.verify_grant = verify_grant
        self.db = self.root / "state.sqlite3"
        with sqlite3.connect(self.db) as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY, data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS grants(id TEXT PRIMARY KEY, session_id TEXT UNIQUE NOT NULL);
                CREATE TABLE IF NOT EXISTS history(seq INTEGER PRIMARY KEY, session_id TEXT, kind TEXT, data TEXT);
                CREATE TABLE IF NOT EXISTS skills(id TEXT, version INTEGER, hash TEXT, data TEXT,
                    PRIMARY KEY(id, version));
            """)

    def get(self, sid):
        identity(sid)
        with sqlite3.connect(self.db) as connection:
            row = connection.execute("SELECT data FROM sessions WHERE id=?", (sid,)).fetchone()
        require(row is not None, "SESSION_NOT_FOUND")
        return json.loads(row[0])

    @contextmanager
    def edit(self, sid, event, *, ended=False):
        with sqlite3.connect(self.db, isolation_level=None, timeout=10) as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                row = connection.execute("SELECT data FROM sessions WHERE id=?", (identity(sid),)).fetchone()
                require(row is not None, "SESSION_NOT_FOUND")
                state = json.loads(row[0])
                require(ended or state["status"] not in TERMINAL, "TERMINAL_SESSION")
                yield state
                connection.execute("UPDATE sessions SET data=? WHERE id=?", (canonical(state), sid))
                connection.execute("INSERT INTO history(session_id,kind,data) VALUES(?,?,?)",
                                   (sid, event, canonical({"at": time.time(), "status": state["status"],
                                    "run": state["run"], "attempt": state["attempt"]})))
                connection.commit()
            except BaseException:
                connection.rollback()
                raise

    def start(self, grant_id):
        grant = self.verify_grant(identity(grant_id))
        sid = identity(grant["session_id"])
        check_ref(grant["request"])
        for ref in grant["references"]:
            check_ref(ref)
        directory = self.root / sid
        require(not directory.exists(), "SESSION_NAMESPACE_COLLISION")
        require(type(grant["bootstrap_calls"]) is int and grant["bootstrap_calls"] > 0, "BOOTSTRAP_LIMIT_REQUIRED")
        state = {"id": sid, "grant": grant, "status": "DIALOGUE", "spec": None,
                 "dialogue": [], "run": 0, "attempt": 0, "workflow": None,
                 "workflows": [], "artifacts": {}, "slots": {}, "reviews": [], "decisions": [],
                 "used": {"frontier": 0, "reviewer": 0, "worker": 0, "diagnostic": 0},
                 "pending": None, "unresolved": {}, "effects": [], "acceptance": None,
                 "delivery": None, "retention": None, "notice": None}
        with sqlite3.connect(self.db) as connection:
            connection.execute("BEGIN IMMEDIATE")
            require(not connection.execute("SELECT 1 FROM grants WHERE id=?", (grant_id,)).fetchone(), "GRANT_ALREADY_CONSUMED")
            require(not connection.execute("SELECT 1 FROM sessions WHERE id=?", (sid,)).fetchone(), "SESSION_ALREADY_EXISTS")
            # Namespace is claimed before any inference or tool effect. A crash leaves
            # the claim for Host reconciliation; no suffix or silent reallocation.
            directory.mkdir()
            connection.execute("INSERT INTO grants VALUES(?,?)", (grant_id, sid))
            connection.execute("INSERT INTO sessions VALUES(?,?)", (sid, canonical(state)))
            connection.commit()
        return self.get(sid)

    def freeze(self, sid, spec):
        require(set(spec) == {"goal", "deliverable_type", "must_haves", "should_haves", "non_goals",
                             "constraints", "criteria", "budget"}, "SPEC_FIELDS")
        require(all(isinstance(spec[k], str) and spec[k].strip() for k in ("goal", "deliverable_type")), "SPEC_GOAL")
        require(all(isinstance(spec[k], list) for k in ("must_haves", "should_haves", "non_goals", "constraints")), "SPEC_LISTS")
        criteria = spec["criteria"]
        require(criteria and len({c["id"] for c in criteria}) == len(criteria), "CRITERIA_REQUIRED")
        for criterion in criteria:
            identity(criterion["id"])
            require(set(criterion) == {"id", "description", "mandatory", "artifact_types"}
                    and criterion["description"] and type(criterion["mandatory"]) is bool
                    and isinstance(criterion["artifact_types"], list) and criterion["artifact_types"], "CRITERION_CONTRACT")
        budget = spec["budget"]
        require(set(budget) == {"frontier", "reviewer", "worker", "diagnostic", "runs", "attempts", "seconds"}
                and all(type(n) is int and n > 0 for n in budget.values()), "FINITE_BUDGET_REQUIRED")
        with self.edit(sid, "SPECIFICATION_FROZEN") as state:
            require(state["status"] == "DIALOGUE" and state["spec"] is None and not state["pending"], "FREEZE_TIMING")
            require(budget["frontier"] >= state["used"]["frontier"], "BUDGET_BELOW_CONSUMED")
            check_ref(state["grant"]["request"])
            for ref in state["grant"]["references"]:
                check_ref(ref)
            state["spec"] = {"value": deepcopy(spec), "hash": digest(spec), "session_id": sid}
            state["status"], state["started_at"] = "ACTIVE", time.time()
            for index, ref in enumerate(state["grant"]["references"]):
                aid = "reference-" + str(index)
                state["artifacts"][aid] = {"id": aid, "type": "reference", "file": ref,
                    "durability": "AUTHORITY", "producer": {"session_id": sid, "run": 0, "attempt": 0},
                    "dependencies": []}
                state["slots"][aid] = aid

    def clarify(self, sid, response_ref):
        check_ref(response_ref)
        with self.edit(sid, "DIALOGUE_RESPONSE") as state:
            require(state["status"] == "DIALOGUE" and not state["pending"], "NOT_IN_DIALOGUE")
            state["dialogue"].append(response_ref)
            state.pop("question", None)

    def skill(self, item):
        required = {"id", "version", "purpose", "inputs", "outputs", "capabilities", "dependencies",
                    "subskills", "known_failures", "provenance", "instructions"}
        require(set(item) == required and item["purpose"] and item["instructions"] and item["provenance"], "SKILL_CONTRACT")
        identity(item["id"])
        require(type(item["version"]) is int and item["version"] > 0, "SKILL_VERSION")
        payload = {"value": item, "hash": digest(item), "status": "CANDIDATE", "successful_uses": []}
        with sqlite3.connect(self.db) as connection:
            row = connection.execute("SELECT hash FROM skills WHERE id=? AND version=?", (item["id"], item["version"])).fetchone()
            if row:
                require(row[0] == payload["hash"], "SKILL_VERSION_COLLISION")
            else:
                connection.execute("INSERT INTO skills VALUES(?,?,?,?)", (item["id"], item["version"], payload["hash"], canonical(payload)))
        return {"id": item["id"], "version": item["version"], "hash": payload["hash"]}

    def skills(self):
        with sqlite3.connect(self.db) as connection:
            return [json.loads(row[0]) for row in connection.execute("SELECT data FROM skills ORDER BY id,version")]

    def check_workflow(self, state, workflow):
        require(set(workflow) == {"version", "stages", "previous_hash", "reason"}, "WORKFLOW_FIELDS")
        stages = workflow["stages"]
        require(stages and len({s["id"] for s in stages}) == len(stages), "STAGES_REQUIRED")
        available = {key: state["artifacts"][aid]["type"] for key, aid in state["slots"].items() if key.startswith("reference-")}
        skills = {(s["value"]["id"], s["value"]["version"]): s for s in self.skills()}
        for stage in stages:
            require(set(stage) == {"id", "tool", "skill", "inputs", "outputs", "parameters", "local_parameters"}, "STAGE_FIELDS")
            identity(stage["id"])
            require(stage["tool"] and isinstance(stage["parameters"], dict) and isinstance(stage["local_parameters"], list), "STAGE_EXECUTION")
            selected = stage["skill"]
            require(skills.get((selected["id"], selected["version"]), {}).get("hash") == selected["hash"], "SKILL_BINDING_CHANGED")
            for slot, kind in stage["inputs"].items():
                require(available.get(slot) == kind, "WORKFLOW_INPUT_CONTRACT")
            require(stage["outputs"] and not set(stage["outputs"]) & set(available), "WORKFLOW_OUTPUT_COLLISION")
            available.update(stage["outputs"])
        require(state["spec"]["value"]["deliverable_type"] in stages[-1]["outputs"].values(), "DELIVERABLE_NOT_PRODUCED")

    def workflow(self, sid, workflow, restart_from, *, local=None):
        with self.edit(sid, "WORKFLOW_RESTART" if local is None else "LOCAL_RETRY") as state:
            require(state["status"] == "ACTIVE" and not state["pending"] and not state["unresolved"], "RESTART_BLOCKED")
            old = state["workflow"]
            self.check_workflow(state, workflow)
            index = next((i for i, s in enumerate(workflow["stages"]) if s["id"] == restart_from), None)
            require(index is not None, "RESTART_POINT_REQUIRED")
            if local is not None:
                require(old == workflow and set(local) <= set(workflow["stages"][index]["local_parameters"]), "LOCAL_TUNING_REQUIRES_REVISION")
                state["attempt"] += 1
            else:
                require(workflow["version"] == state["run"] + 1 and workflow["previous_hash"] == (digest(old) if old else None)
                        and workflow["reason"], "WORKFLOW_VERSION_LINEAGE")
                require(old is None or strategy_hash(old) != strategy_hash(workflow), "LOCAL_CORRECTION_REQUIRES_ATTEMPT")
                state["workflows"].append(deepcopy(workflow))
                state["run"] += 1
                state["attempt"] = 1
            budget = state["spec"]["value"]["budget"]
            require(state["run"] <= budget["runs"] and state["attempt"] <= budget["attempts"], "RUN_ATTEMPT_BUDGET")
            retained = {k: v for k, v in state["slots"].items() if k.startswith("reference-")}
            for i in range(index):
                require(old is not None and i < len(old["stages"]) and old["stages"][i] == workflow["stages"][i], "CHECKPOINT_STRATEGY_CHANGED")
                for slot in workflow["stages"][i]["outputs"]:
                    aid = state["slots"].get(slot)
                    require(aid and state["artifacts"][aid]["durability"] in {"CHECKPOINT", "OUTPUT"}, "CHECKPOINT_MISSING")
                    self.check_artifact(state, aid)
                    require(all(dep in retained.values() for dep in state["artifacts"][aid]["dependencies"]), "CHECKPOINT_DEPENDENCY_CHANGED")
                    retained[slot] = aid
            state["slots"], state["reviews"] = retained, []
            state["workflow"], state["cursor"] = deepcopy(workflow), index
            state["local"] = deepcopy(local or {})

    def check_artifact(self, state, aid):
        artifact = state["artifacts"][aid]
        require(artifact["producer"]["session_id"] == state["id"], "ARTIFACT_SESSION_MISMATCH")
        check_ref(artifact["file"])
        for dependency in artifact["dependencies"]:
            self.check_artifact(state, dependency)
        return artifact

    def reserve(self, sid, role, request):
        require(role in {"frontier", "reviewer", "worker", "diagnostic"}, "INVALID_ROLE")
        with self.edit(sid, "EFFECT_RESERVED") as state:
            require(state["status"] in {"DIALOGUE", "ACTIVE"} and not state["pending"], "EFFECT_IN_FLIGHT")
            require(role == "frontier" or not state["unresolved"], "UNRESOLVED_EFFECT")
            if state["spec"]:
                limit = state["spec"]["value"]["budget"][role]
                require(time.time() - state["started_at"] < state["spec"]["value"]["budget"]["seconds"], "SESSION_TIME_BUDGET")
            else:
                require(role == "frontier", "DIALOGUE_ONLY_FRONTIER")
                limit = state["grant"]["bootstrap_calls"]
            require(state["used"][role] < limit, "CALL_BUDGET_EXHAUSTED")
            if role in {"worker", "diagnostic"}:
                require(state["workflow"] is not None, "WORKFLOW_REQUIRED")
                for aid in request["input_ids"]:
                    require(aid in state["slots"].values(), "STALE_WORK_INPUT")
                    self.check_artifact(state, aid)
            state["used"][role] += 1
            ticket = {"id": uuid.uuid4().hex, "role": role, "run": state["run"], "attempt": state["attempt"],
                      "spec_hash": state["spec"]["hash"] if state["spec"] else None,
                      "workflow_hash": digest(state["workflow"]), "request": deepcopy(request), "at": time.time()}
            state["pending"] = ticket
        directory = self.root / sid / "calls" / ticket["id"]
        directory.mkdir(parents=True)
        ticket["directory"] = str(directory)
        write_once(directory / "request.json", ticket)
        return ticket

    def settle(self, sid, ticket, result):
        require(result["status"] in {"SUCCESS", "FAILED", "UNRESOLVED"}, "EFFECT_STATUS")
        with self.edit(sid, "EFFECT_OBSERVED") as state:
            require(state["pending"] and state["pending"]["id"] == ticket["id"], "EFFECT_TICKET_MISMATCH")
            check_ref(result["report"])
            report = json.loads(check_ref(result["report"]).read_text(encoding="utf-8"))
            require(report["ticket_id"] == ticket["id"] and report["status"] == result["status"], "INVOCATION_BINDING")
            if ticket["role"] in {"frontier", "reviewer"}:
                require(report["role"] == ticket["role"] and report["mode"] == "ACTUAL", "INDEPENDENT_ROLE_REQUIRED")
            observation = {"ticket": ticket, "result": deepcopy(result)}
            state["effects"].append(observation)
            state["pending"] = None
            if result["status"] == "UNRESOLVED":
                state["unresolved"][ticket["id"]] = observation
            if result["status"] != "SUCCESS":
                state["failure"] = observation
                return
            if ticket["role"] in {"worker", "diagnostic"}:
                self.register_outputs(state, ticket, result["outputs"])
            if ticket["role"] == "reviewer":
                try:
                    self.register_review(state, ticket, result["value"], result["report"])
                except (ContractError, KeyError, TypeError) as exc:
                    state["failure"] = {"kind": "REVIEW_CONTRACT", "reason": str(exc), "observation": observation}

    def register_outputs(self, state, ticket, outputs):
        expected = ticket["request"]["outputs"]
        require(set(outputs) == set(expected), "WORKER_OUTPUT_CONTRACT")
        for slot, ref in outputs.items():
            check_ref(ref)
            aid = ticket["id"] + "-" + identity(slot)
            state["artifacts"][aid] = {"id": aid, "type": expected[slot], "file": ref,
                "durability": ticket["request"].get("durability", "CHECKPOINT"),
                "producer": {"session_id": state["id"], "run": state["run"], "attempt": state["attempt"], "stage": ticket["request"]["stage_id"]},
                "dependencies": ticket["request"]["input_ids"]}
            require(state["artifacts"][aid]["durability"] in DURABILITY, "DURABILITY_INVALID")
            state["slots"][slot] = aid
        state["reviews"] = []
        if ticket["role"] == "worker":
            state["cursor"] += 1
            state["local"] = {}

    def register_review(self, state, ticket, review, invocation):
        request = ticket["request"]
        require(ticket["spec_hash"] == state["spec"]["hash"] and ticket["workflow_hash"] == digest(state["workflow"])
                and ticket["run"] == state["run"] and ticket["attempt"] == state["attempt"], "STALE_REVIEW")
        require(set(review) == {"outcomes", "observations", "requested_evidence"}, "REVIEW_FIELDS")
        expected = {c["id"] for c in request["criteria"]}
        outcomes = review["outcomes"]
        require({c["id"] for c in outcomes} == expected and len(outcomes) == len(expected), "REVIEW_COVERAGE")
        for outcome in outcomes:
            require(outcome["outcome"] in {"MET", "UNMET", "UNCERTAIN"} and outcome["reason"], "REVIEW_OUTCOME")
        for aid in request["artifact_ids"]:
            require(aid in state["slots"].values(), "STALE_REVIEW_ARTIFACT")
            self.check_artifact(state, aid)
        state["reviews"].append({"value": review, "artifact_ids": request["artifact_ids"],
                                 "invocation": invocation, "ticket": ticket["id"]})

    def decision(self, sid, ticket, value):
        require(ticket["role"] == "frontier" and value["reason"], "FRONTIER_DECISION_REQUIRED")
        with self.edit(sid, "FRONTIER_DECISION") as state:
            require(any(e["ticket"]["id"] == ticket["id"] and e["result"]["status"] == "SUCCESS" for e in state["effects"]), "DECISION_INVOCATION_REQUIRED")
            state["decisions"].append({"ticket": ticket["id"], "value": value})

    def accept(self, sid):
        with self.edit(sid, "INTERNAL_ACCEPT") as state:
            require(state["status"] == "ACTIVE" and not state["pending"] and not state["unresolved"], "ACCEPT_UNRESOLVED")
            require(state["decisions"] and state["decisions"][-1]["value"]["action"] == "ACCEPT", "ACCEPT_DECISION_REQUIRED")
            require(state["cursor"] == len(state["workflow"]["stages"]), "WORKFLOW_INCOMPLETE")
            final = [aid for aid in state["slots"].values() if state["artifacts"][aid]["type"] == state["spec"]["value"]["deliverable_type"]]
            require(final, "FINAL_ARTIFACT_MISSING")
            for aid in final:
                self.check_artifact(state, aid)
            mandatory = {c["id"] for c in state["spec"]["value"]["criteria"] if c["mandatory"]}
            met = set()
            final_reviewed = set()
            for review in state["reviews"]:
                check_ref(review["invocation"])
                for aid in review["artifact_ids"]:
                    require(aid in state["slots"].values(), "STALE_ACCEPT_REVIEW")
                    self.check_artifact(state, aid)
                met.update(o["id"] for o in review["value"]["outcomes"] if o["outcome"] == "MET")
                require(not any(o["id"] in mandatory and o["outcome"] != "MET" for o in review["value"]["outcomes"]), "MANDATORY_NOT_MET")
                final_reviewed.update(review["artifact_ids"])
            require(mandatory <= met and set(final) <= final_reviewed, "ACCEPT_COVERAGE_MISSING")
            state["acceptance"] = {"artifact_ids": final, "review_tickets": [r["ticket"] for r in state["reviews"]],
                                   "spec_hash": state["spec"]["hash"], "workflow_hash": digest(state["workflow"])}
            state["status"] = "ACCEPTED"

    def close(self, sid, status, reason, receipt=None):
        require(status in TERMINAL and reason, "TERMINAL_REASON_REQUIRED")
        with self.edit(sid, status) as state:
            if status == "CLOSED":
                require(state["status"] == "ACCEPTED" and receipt is not None, "DELIVERY_RECEIPT_REQUIRED")
                check_ref(receipt)
                state["delivery"] = receipt
            state["status"], state["terminal_reason"] = status, reason
            candidates = state["acceptance"]["artifact_ids"] if state["acceptance"] else [
                aid for aid in state["slots"].values() if state["artifacts"][aid]["durability"] == "OUTPUT"]
            state["notice"] = {"abnormal_termination": status != "CLOSED", "undelivered_artifacts": [] if status == "CLOSED" else
                [state["artifacts"][aid] for aid in candidates], "internally_accepted": state["acceptance"] is not None,
                "required_host_action": "ANNOUNCE_UNDELIVERED_ARTIFACTS" if candidates and status != "CLOSED" else None,
                "session_reexecution_allowed": False}
            state["retention"] = {"keep": list(state["artifacts"]), "prune": [], "reason": "Protect authority, output, checkpoints and failure lineage."}

    def promote(self, sid):
        state = self.get(sid)
        require(state["acceptance"] and state["grant"]["mode"] == "ACTUAL", "ACTUAL_SUCCESS_REQUIRED")
        with sqlite3.connect(self.db) as connection:
            for stage in state["workflow"]["stages"]:
                selected = stage["skill"]
                row = connection.execute("SELECT data FROM skills WHERE id=? AND version=?", (selected["id"], selected["version"])).fetchone()
                skill = json.loads(row[0])
                require(skill["hash"] == selected["hash"], "SKILL_CHANGED")
                use = {"session_id": sid, "acceptance_hash": digest(state["acceptance"]), "stage": stage["id"]}
                if use not in skill["successful_uses"]:
                    skill["successful_uses"].append(use)
                skill["status"] = "VALIDATED"
                connection.execute("UPDATE skills SET data=? WHERE id=? AND version=?", (canonical(skill), selected["id"], selected["version"]))

    def recover(self, sid, ticket_id, observed_result):
        """Use an independently observed outcome; never redispatch a reserved effect."""
        with self.edit(sid, "RECOVERY_OBSERVATION") as state:
            pending = state["pending"]
            unresolved = state["unresolved"].get(ticket_id)
            require((pending and pending["id"] == ticket_id) or unresolved, "RECOVERY_TICKET_NOT_FOUND")
            ticket = pending or unresolved["ticket"]
            require(observed_result["status"] in {"SUCCESS", "FAILED"}, "RECOVERY_NOT_RESOLVED")
            check_ref(observed_result["report"])
            report = json.loads(check_ref(observed_result["report"]).read_text(encoding="utf-8"))
            require(report["ticket_id"] == ticket_id and report["status"] == observed_result["status"], "RECOVERY_INVOCATION_BINDING")
            if observed_result["status"] == "SUCCESS" and ticket["role"] in {"worker", "diagnostic"}:
                self.register_outputs(state, ticket, observed_result["outputs"])
            elif observed_result["status"] == "SUCCESS" and ticket["role"] == "reviewer":
                self.register_review(state, ticket, observed_result["value"], observed_result["report"])
            state["pending"] = None
            state["unresolved"].pop(ticket_id, None)
            state["effects"].append({"ticket": ticket, "result": observed_result, "recovery": True})

    def retention(self, sid, proposal):
        state = self.get(sid)
        require(state["status"] in TERMINAL and proposal["reason"], "RETENTION_ONLY_AFTER_END")
        current = set(state["slots"].values())
        for artifact in state["artifacts"].values():
            current.update(artifact["dependencies"])
        protected = current | {aid for aid, a in state["artifacts"].items() if a["durability"] in {"AUTHORITY", "OUTPUT"}}
        protected.update(aid for review in state["reviews"] for aid in review["artifact_ids"])
        requested = set(proposal["prune"])
        require(requested <= set(state["artifacts"]) and not requested & protected, "RETENTION_PROTECTED_ARTIFACT")
        require(all(state["artifacts"][aid]["durability"] == "TRANSIENT" for aid in requested), "RETENTION_REQUIRES_TRANSIENT_OWNERSHIP")
        with self.edit(sid, "RETENTION_DECISION", ended=True) as current_state:
            current_state["retention"] = {"keep": sorted(set(state["artifacts"]) - requested), "prune": sorted(requested), "reason": proposal["reason"]}
