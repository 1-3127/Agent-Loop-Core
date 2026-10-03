"""Authority, lifecycle and lineage in one transactional Session store.

No model, Host, network or domain execution code belongs in this module.
"""
from contextlib import contextmanager, nullcontext
from contextvars import ContextVar
from copy import deepcopy
import hashlib
import json
import os
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
    return digest({"stages": stages, "final_bindings": workflow["final_bindings"]}) if workflow.get("final_bindings") else digest(stages)


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
        self.transaction = ContextVar("session_transaction", default=None)
        with sqlite3.connect(self.db) as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY, data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS grants(id TEXT PRIMARY KEY, session_id TEXT UNIQUE NOT NULL);
                CREATE TABLE IF NOT EXISTS history(seq INTEGER PRIMARY KEY, session_id TEXT, kind TEXT, data TEXT);
                CREATE TABLE IF NOT EXISTS skills(id TEXT, version INTEGER, hash TEXT, data TEXT,
                    PRIMARY KEY(id, version));
                CREATE TABLE IF NOT EXISTS promotion(id TEXT PRIMARY KEY, session_id TEXT, kind TEXT, data TEXT);
            """)

    def get(self, sid):
        identity(sid)
        active = self.transaction.get()
        if active:
            require(active[0] == sid, "CROSS_SESSION_TRANSACTION")
            return active[1]
        with sqlite3.connect(self.db) as connection:
            row = connection.execute("SELECT data FROM sessions WHERE id=?", (sid,)).fetchone()
        require(row is not None, "SESSION_NOT_FOUND")
        state = json.loads(row[0])
        try:
            self.project(state)
        except OSError as exc:
            state["projection_error"] = str(exc)
        return state

    def project(self, state):
        """Regenerable projections; SQLite/revision remains the only state authority."""
        directory = self.root / state["id"]
        if not directory.is_dir():
            return
        def snapshot(path, value):
            path.parent.mkdir(parents=True, exist_ok=True)
            text = canonical(value) + "\n"
            if path.is_file() and path.read_text(encoding="utf-8") == text:
                return
            temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
            temporary.write_text(text, encoding="utf-8", newline="\n")
            os.replace(temporary, path)
        binding = {"session_id": state["id"], "revision": state.get("revision", 0),
                   "authority": "state.sqlite3", "run": state["run"], "attempt": state["attempt"]}
        snapshot(directory / "state.json", {**binding, "state": state})
        with sqlite3.connect(self.db) as connection:
            assessments = connection.execute("SELECT rowid,data FROM promotion WHERE session_id=? ORDER BY rowid", (state["id"],)).fetchall()
        snapshot(directory / "promotion.json", {"authority": "state.sqlite3/promotion", "session_id": state["id"],
            "ledger_revision": assessments[-1][0] if assessments else 0,
            "events": [json.loads(row[1]) for row in assessments]})
        if state["spec"]:
            snapshot(directory / "specification.json", state["spec"])
        if state["workflow"]:
            for workflow in state["workflows"]:
                snapshot(directory / "runs" / ("run-%04d" % workflow["version"]) / "workflow.json",
                         {"hash": digest(workflow), "value": workflow})
            run = directory / "runs" / ("run-%04d" % state["run"])
            snapshot(run / "workflow.json", {"hash": digest(state["workflow"]), "value": state["workflow"]})
            attempt = run / "attempts" / ("attempt-%04d" % state["attempt"])
            snapshot(attempt / "evidence.json", {**binding, "spec_hash": state["spec"]["hash"],
                "workflow_hash": digest(state["workflow"]), "slots": state["slots"], "artifacts": state["artifacts"]})
            for review in state["reviews"]:
                owner = directory / "runs" / ("run-%04d" % review["run"]) / "attempts" / ("attempt-%04d" % review["attempt"])
                snapshot(owner / "reviews" / (review["ticket"] + ".json"), review)
        summary = directory / "summary.md"
        summary.write_text("# Session " + state["id"] + "\n\n" +
            f"Status: {state['status']}; revision: {state.get('revision', 0)}; Run/Attempt: {state['run']}/{state['attempt']}.\n\n" +
            "SQLite is authoritative. See state.json for application, effect, acceptance and delivery records.\n",
            encoding="utf-8", newline="\n")

    @contextmanager
    def edit(self, sid, event, *, ended=False):
        active = self.transaction.get()
        if active:
            require(active[0] == sid, "CROSS_SESSION_TRANSACTION")
            require(ended or active[1]["status"] not in TERMINAL, "TERMINAL_SESSION")
            yield active[1]
            return
        with sqlite3.connect(self.db, isolation_level=None, timeout=10) as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                row = connection.execute("SELECT data FROM sessions WHERE id=?", (identity(sid),)).fetchone()
                require(row is not None, "SESSION_NOT_FOUND")
                state = json.loads(row[0])
                require(ended or state["status"] not in TERMINAL, "TERMINAL_SESSION")
                token = self.transaction.set((sid, state, connection))
                try:
                    yield state
                finally:
                    self.transaction.reset(token)
                state["revision"] = state.get("revision", 0) + 1
                connection.execute("UPDATE sessions SET data=? WHERE id=?", (canonical(state), sid))
                connection.execute("INSERT INTO history(session_id,kind,data) VALUES(?,?,?)",
                                   (sid, event, canonical({"at": time.time(), "status": state["status"],
                                    "run": state["run"], "attempt": state["attempt"], "revision": state["revision"],
                                    "application": {k: v for k, v in (state.get("application") or {}).items() if k != "value"}})))
                connection.commit()
            except BaseException:
                connection.rollback()
                raise
        try:
            self.project(state)
        except OSError:
            # The committed DB marker must never be reported as rolled back.
            # A subsequent status read repairs the view or exposes projection_error.
            pass

    @contextmanager
    def application(self, sid, ticket_id):
        """Pure Core changes commit with their marker; effect dispatch follows commit."""
        with self.edit(sid, "DECISION_APPLICATION") as state:
            application = state.get("application")
            require(application and application["ticket_id"] == ticket_id and
                    application["phase"] == "PREPARED", "DECISION_NOT_PREPARED")
            application["phase"] = "APPLYING"
            yield state
            application["phase"] = "APPLYING" if state["pending"] else "APPLIED"

    def reject(self, sid, reason):
        with self.edit(sid, "DECISION_REJECTED") as state:
            application = state.get("application")
            require(application and application["phase"] == "PREPARED", "CANNOT_REJECT_DISPATCHED_DECISION")
            application.update(phase="REJECTED", rejection=reason)
            state["failure"] = {"kind": "CONTRACT", "reason": reason, "decision": application["value"]}

    def prepare_decision(self, state, ticket, value):
        require(ticket["role"] == "frontier" and value["reason"], "FRONTIER_DECISION_REQUIRED")
        previous = state.get("application")
        require(not previous or previous["phase"] in {"APPLIED", "REJECTED"}, "DECISION_APPLICATION_INCOMPLETE")
        decision = {"ticket": ticket["id"], "value": deepcopy(value)}
        state["decisions"].append(decision)
        state["application"] = {"ticket_id": ticket["id"], "phase": "PREPARED", "value": deepcopy(value), "effect_ticket_id": None}

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
                 "delivery": None, "retention": None, "notice": None, "application": None, "revision": 0}
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
            require(set(criterion) == {"id", "description", "mandatory", "artifact_types", "evidence_slots"}
                    and criterion["description"] and type(criterion["mandatory"]) is bool
                    and isinstance(criterion["artifact_types"], list) and criterion["artifact_types"], "CRITERION_CONTRACT")
            require(isinstance(criterion["evidence_slots"], dict) and criterion["evidence_slots"] and
                    set(criterion["evidence_slots"].values()) == set(criterion["artifact_types"]), "CRITERION_EVIDENCE_REQUIRED")
            for slot, kind in criterion["evidence_slots"].items():
                identity(slot)
                require(isinstance(kind, str) and kind.strip(), "EVIDENCE_TYPE_REQUIRED")
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
        active = self.transaction.get()
        with (nullcontext(active[2]) if active else sqlite3.connect(self.db)) as connection:
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
        require({"version", "stages", "previous_hash", "reason"} <= set(workflow) <= {"version", "stages", "previous_hash", "reason", "final_bindings"}, "WORKFLOW_FIELDS")
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
                identity(slot)
                require(available.get(slot) == kind, "WORKFLOW_INPUT_CONTRACT")
            require(stage["outputs"] and not set(stage["outputs"]) & set(available), "WORKFLOW_OUTPUT_COLLISION")
            for slot, kind in stage["outputs"].items():
                identity(slot)
                require(isinstance(kind, str) and kind.strip(), "WORKFLOW_OUTPUT_TYPE")
            available.update(stage["outputs"])
        require(any(state["spec"]["value"]["deliverable_type"] in stage["outputs"].values() for stage in stages), "DELIVERABLE_NOT_PRODUCED")
        bindings = workflow.get("final_bindings", {})
        require(isinstance(bindings, dict), "FINAL_BINDINGS_FIELDS")
        evidence = {slot: kind for criterion in state["spec"]["value"]["criteria"] for slot, kind in criterion["evidence_slots"].items()}
        preserved = set()
        for target, binding in bindings.items():
            identity(target)
            require(isinstance(binding, dict) and set(binding) == {"source", "preserve_as"}, "FINAL_BINDING_FIELDS")
            source, prior = identity(binding["source"]), identity(binding["preserve_as"])
            kind = state["spec"]["value"]["deliverable_type"]
            require(evidence.get(target) == kind and available.get(target) == kind and available.get(source) == kind and source != target, "FINAL_BINDING_TYPE")
            require(prior not in available and prior not in preserved and not prior.startswith("reference-"), "FINAL_BINDING_PRESERVE_COLLISION")
            require(source not in bindings, "FINAL_BINDING_CHAIN_FORBIDDEN")
            preserved.add(prior)

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
            previous_slots = dict(state["slots"])
            if old and state["cursor"] == len(old["stages"]):
                for target, binding in old.get("final_bindings", {}).items():
                    require(binding["preserve_as"] in previous_slots, "FINAL_BINDING_ORIGIN_MISSING")
                    previous_slots[target] = previous_slots[binding["preserve_as"]]
            for i in range(index):
                require(old is not None and i < len(old["stages"]) and old["stages"][i] == workflow["stages"][i], "CHECKPOINT_STRATEGY_CHANGED")
                for slot in workflow["stages"][i]["outputs"]:
                    aid = previous_slots.get(slot)
                    require(aid and state["artifacts"][aid]["durability"] in {"CHECKPOINT", "OUTPUT"}, "CHECKPOINT_MISSING")
                    self.check_artifact(state, aid)
                    require(all(dep in retained.values() for dep in state["artifacts"][aid]["dependencies"]), "CHECKPOINT_DEPENDENCY_CHANGED")
                    retained[slot] = aid
            state["slots"] = retained
            state["workflow"], state["cursor"] = deepcopy(workflow), index
            state["local"] = deepcopy(local or {})

    def check_artifact(self, state, aid):
        artifact = state["artifacts"][aid]
        require(artifact["producer"]["session_id"] == state["id"], "ARTIFACT_SESSION_MISMATCH")
        check_ref(artifact["file"])
        for dependency in artifact["dependencies"]:
            self.check_artifact(state, dependency)
        return artifact

    def evidence_binding(self, state, criterion):
        evidence = []
        for slot, kind in criterion["evidence_slots"].items():
            aid = state["slots"].get(slot)
            require(aid is not None, "CRITERION_EVIDENCE_MISSING: " + slot)
            artifact = self.check_artifact(state, aid)
            require(artifact["type"] == kind, "CRITERION_EVIDENCE_TYPE")
            dependencies = {}
            def collect(current):
                for dep in state["artifacts"][current]["dependencies"]:
                    require(dep in state["slots"].values(), "STALE_EVIDENCE_DEPENDENCY")
                    if dep not in dependencies:
                        dependencies[dep] = self.check_artifact(state, dep)["file"]
                        collect(dep)
            collect(aid)
            evidence.append({"slot": slot, "artifact_id": aid, "file": artifact["file"], "dependencies": dependencies})
        return {"criterion_id": criterion["id"], "spec_hash": state["spec"]["hash"],
            "workflow_hash": digest(state["workflow"]), "run": state["run"], "attempt": state["attempt"], "evidence": evidence}

    def current_reviews(self, state):
        criteria = {c["id"]: c for c in state["spec"]["value"]["criteria"]} if state["spec"] else {}
        current = []
        for review in state["reviews"]:
            try:
                check_ref(review["invocation"])
                require(all(binding == self.evidence_binding(state, criteria[binding["criterion_id"]])
                            for binding in review["bindings"]), "STALE_REVIEW_BINDING")
                current.append(review)
            except (ContractError, KeyError, OSError):
                continue
        return current

    def reserve(self, sid, role, request):
        require(role in {"frontier", "reviewer", "worker", "diagnostic"}, "INVALID_ROLE")
        with self.edit(sid, "EFFECT_RESERVED") as state:
            require(state["status"] in {"DIALOGUE", "ACTIVE"} and not state["pending"], "EFFECT_IN_FLIGHT")
            require(role == "frontier" or not state["unresolved"], "UNRESOLVED_EFFECT")
            application = state.get("application")
            if role == "frontier":
                require(not application or application["phase"] in {"APPLIED", "REJECTED"}, "DECISION_APPLICATION_INCOMPLETE")
            else:
                require(application and application["phase"] == "APPLYING", "EFFECT_DECISION_REQUIRED")
            if state["spec"]:
                limit = state["spec"]["value"]["budget"][role]
                require(time.time() - state["started_at"] < state["spec"]["value"]["budget"]["seconds"], "SESSION_TIME_BUDGET")
            else:
                require(role == "frontier", "DIALOGUE_ONLY_FRONTIER")
                limit = state["grant"]["bootstrap_calls"]
            require(state["used"][role] < limit, "CALL_BUDGET_EXHAUSTED")
            if role in {"worker", "diagnostic"}:
                require(state["workflow"] is not None, "WORKFLOW_REQUIRED")
                require(request["outputs"], "OUTPUT_SLOTS_REQUIRED")
                for slot, kind in request["outputs"].items():
                    identity(slot)
                    require(isinstance(kind, str) and kind.strip(), "OUTPUT_TYPE_REQUIRED")
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
            if role != "frontier":
                ticket["decision_ticket_id"] = application["ticket_id"]
                application["effect_ticket_id"] = ticket["id"]
            write_once(directory / "request.json", ticket)
            if request.get("skill"):
                from .promotion import Promotion
                Promotion.append(self.transaction.get()[2], "selection-" + ticket["id"], "SELECTION", state,
                    {"skill": request["skill"], "ticket_id": ticket["id"], "task": state["spec"]["value"]["goal"],
                     "spec_hash": ticket["spec_hash"], "workflow_hash": ticket["workflow_hash"],
                     "run": ticket["run"], "attempt": ticket["attempt"], "stage": request["stage_id"],
                     "execution_observed": None})
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
            if ticket["role"] != "frontier" and state.get("application"):
                require(state["application"]["effect_ticket_id"] == ticket["id"], "APPLICATION_EFFECT_MISMATCH")
                state["application"]["phase"] = "APPLIED"
            if ticket["role"] == "frontier":
                if result["status"] == "SUCCESS":
                    self.prepare_decision(state, ticket, result["value"])
                else:
                    state["host_request"] = {"reason": "Frontier inference failed. Host owns this layer.", "ticket_id": ticket["id"]}
            if ticket["role"] == "worker":
                from .promotion import Promotion
                Promotion.use(self.transaction.get()[2], state, ticket, result)
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
                "producer": {"session_id": state["id"], "run": state["run"], "attempt": state["attempt"], "stage": ticket["request"]["stage_id"], "ticket_id": ticket["id"]},
                "dependencies": ticket["request"]["input_ids"]}
            require(state["artifacts"][aid]["durability"] in DURABILITY, "DURABILITY_INVALID")
            state["slots"][slot] = aid
        if ticket["role"] == "worker":
            state["cursor"] += 1
            state["local"] = {}
            if state["cursor"] == len(state["workflow"]["stages"]):
                for target, binding in state["workflow"].get("final_bindings", {}).items():
                    source, prior = binding["source"], binding["preserve_as"]
                    require(prior not in state["slots"], "FINAL_BINDING_PRESERVE_COLLISION")
                    before, after = state["slots"][target], state["slots"][source]
                    require(state["artifacts"][before]["type"] == state["artifacts"][after]["type"] == state["spec"]["value"]["deliverable_type"], "FINAL_BINDING_TYPE")
                    self.check_artifact(state, before)
                    self.check_artifact(state, after)
                    state["slots"][prior], state["slots"][target] = before, after

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
        require(request["bindings"] == [self.evidence_binding(state, c) for c in request["criteria"]], "REVIEW_EVIDENCE_BINDING")
        require({e["artifact_id"] for b in request["bindings"] for e in b["evidence"]} <= set(request["artifact_ids"]), "REVIEW_EVIDENCE_COVERAGE")
        state["reviews"].append({"value": review, "artifact_ids": request["artifact_ids"],
                                 "invocation": invocation, "ticket": ticket["id"], "bindings": request["bindings"],
                                 "run": ticket["run"], "attempt": ticket["attempt"]})

    def accept(self, sid):
        with self.edit(sid, "INTERNAL_ACCEPT") as state:
            require(state["status"] == "ACTIVE" and not state["pending"] and not state["unresolved"], "ACCEPT_UNRESOLVED")
            require(state["decisions"] and state["decisions"][-1]["value"]["action"] == "ACCEPT", "ACCEPT_DECISION_REQUIRED")
            require(state["cursor"] == len(state["workflow"]["stages"]), "WORKFLOW_INCOMPLETE")
            final = list(dict.fromkeys(state["slots"][slot] for slot in state["workflow"]["final_bindings"])) if state["workflow"].get("final_bindings") else [aid for aid in state["slots"].values() if state["artifacts"][aid]["type"] == state["spec"]["value"]["deliverable_type"]]
            require(final, "FINAL_ARTIFACT_MISSING")
            for aid in final:
                self.check_artifact(state, aid)
            mandatory = {c["id"] for c in state["spec"]["value"]["criteria"] if c["mandatory"]}
            outcomes = {}
            final_reviewed = set()
            reviews = self.current_reviews(state)
            for review in reviews:
                check_ref(review["invocation"])
                outcomes.update({o["id"]: o["outcome"] for o in review["value"]["outcomes"]})
                final_reviewed.update(e["artifact_id"] for binding in review["bindings"] for e in binding["evidence"])
            require(all(outcomes.get(cid) == "MET" for cid in mandatory) and set(final) <= final_reviewed, "ACCEPT_COVERAGE_MISSING")
            state["acceptance"] = {"artifact_ids": final, "review_tickets": [r["ticket"] for r in reviews],
                                   "spec_hash": state["spec"]["hash"], "workflow_hash": digest(state["workflow"])}
            state["status"] = "ACCEPTED"
            from .promotion import Promotion
            Promotion.final(self.transaction.get()[2], state)

    def close(self, sid, status, reason, receipt=None):
        require(status in TERMINAL and reason, "TERMINAL_REASON_REQUIRED")
        with self.edit(sid, status) as state:
            if status == "CLOSED":
                require(state["status"] == "ACCEPTED" and receipt is not None, "DELIVERY_RECEIPT_REQUIRED")
                check_ref(receipt)
                state["delivery"] = receipt
                from .promotion import Promotion
                Promotion.append(self.transaction.get()[2], "export-" + sid, "LOCAL_EXPORT", state,
                    {"receipt": receipt, "artifact_ids": state["acceptance"]["artifact_ids"],
                     "actual_user_delivery": "UNOBSERVED", "user_quality": "UNOBSERVED"})
            state["status"], state["terminal_reason"] = status, reason
            candidates = state["acceptance"]["artifact_ids"] if state["acceptance"] else [
                aid for aid in state["slots"].values() if state["artifacts"][aid]["durability"] == "OUTPUT"]
            state["notice"] = {"abnormal_termination": True if status != "CLOSED" else None, "undelivered_artifacts":
                [state["artifacts"][aid] for aid in candidates], "internally_accepted": state["acceptance"] is not None,
                "user_delivery_observed": False,
                "required_host_action": "ANNOUNCE_UNDELIVERED_ARTIFACTS" if candidates else None,
                "session_reexecution_allowed": False}
            state["retention"] = {"keep": list(state["artifacts"]), "prune": [], "reason": "Protect authority, output, checkpoints and failure lineage."}

    def promotion_decision(self, sid, payload, reason):
        selected = payload["skill"]
        require(any({"id": s["value"]["id"], "version": s["value"]["version"], "hash": s["hash"]} == selected
                    for s in self.skills()), "PROMOTION_SKILL_BINDING")
        require(isinstance(payload["judgment"], str) and payload["judgment"].strip() and reason, "PROMOTION_JUDGMENT_REQUIRED")
        with self.edit(sid, "PROMOTION_DECISION") as state:
            require(state["spec"] is not None, "PROMOTION_TASK_REQUIRED")
            from .promotion import Promotion
            Promotion.append(self.transaction.get()[2], "judgment-" + state["application"]["ticket_id"],
                "FRONTIER_JUDGMENT", state, {"skill": selected, "task": state["spec"]["value"]["goal"],
                "spec_hash": state["spec"]["hash"], "judgment": payload["judgment"], "reason": reason,
                "decision_ticket_id": state["application"]["ticket_id"]})

    def assessment(self, sid, receipt_id, item, receipt_ref):
        """Append Host facts outside execution state, including after terminal."""
        state = self.get(sid)
        scope = item["scope"]
        require(scope["kind"] in {"WORKFLOW", "ARTIFACT", "SKILL"}, "ASSESSMENT_SCOPE")
        if scope["kind"] == "WORKFLOW":
            require(any(digest(w) == scope["workflow_hash"] for w in state["workflows"]), "ASSESSMENT_WORKFLOW_BINDING")
        elif scope["kind"] == "ARTIFACT":
            require(scope["artifact_ids"] and all(a in state["artifacts"] for a in scope["artifact_ids"]), "ASSESSMENT_ARTIFACT_BINDING")
        else:
            require(any(e["ticket"]["request"].get("skill") == scope["skill"] for e in state["effects"]), "ASSESSMENT_SKILL_BINDING")
        require(item["kind"] in {"DELIVERY", "USER_FEEDBACK"}, "ASSESSMENT_KIND")
        if item["kind"] == "DELIVERY":
            require(scope["kind"] == "ARTIFACT", "DELIVERY_ARTIFACT_SCOPE_REQUIRED")
            for aid in scope["artifact_ids"]:
                self.check_artifact(state, aid)
        from .promotion import Promotion
        with sqlite3.connect(self.db) as connection:
            Promotion.append(connection, "host-" + identity(receipt_id), item["kind"], state,
                {"scope": scope, "receipt": receipt_ref, "original_user_evidence": item.get("user_evidence"),
                 "presentation": item.get("presentation"), "text": item.get("text"),
                 "scope_does_not_expand_to_participating_skills": True})

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
            if ticket["role"] in {"frontier", "reviewer"}:
                require(report["role"] == ticket["role"] and report["mode"] == "ACTUAL", "INDEPENDENT_ROLE_REQUIRED")
            if observed_result["status"] == "SUCCESS" and ticket["role"] in {"worker", "diagnostic"}:
                self.register_outputs(state, ticket, observed_result["outputs"])
            elif observed_result["status"] == "SUCCESS" and ticket["role"] == "reviewer":
                self.register_review(state, ticket, observed_result["value"], observed_result["report"])
            state["pending"] = None
            state["unresolved"].pop(ticket_id, None)
            state["effects"].append({"ticket": ticket, "result": observed_result, "recovery": True})
            if ticket["role"] == "frontier" and observed_result["status"] == "SUCCESS":
                self.prepare_decision(state, ticket, observed_result["value"])
            elif ticket["role"] != "frontier":
                application = state.get("application")
                if application and application["effect_ticket_id"] == ticket_id:
                    application["phase"] = "APPLIED"
            if observed_result["status"] == "FAILED":
                state["failure"] = {"ticket": ticket, "result": observed_result, "recovery": True}
            if ticket["role"] == "worker":
                from .promotion import Promotion
                # Original uncertain and subsequently observed results are separate facts.
                Promotion.append(self.transaction.get()[2], "recovery-" + ticket_id, "USE_OBSERVATION", state,
                    {"skill": ticket["request"].get("skill"), "ticket_id": ticket_id, "outcome": observed_result["status"],
                     "invocation": observed_result["report"], "artifacts": observed_result.get("outputs", {}),
                     "execution_observed": report.get("execution_observed"), "task": state["spec"]["value"]["goal"],
                     "spec_hash": ticket["spec_hash"], "workflow_hash": ticket["workflow_hash"],
                     "run": ticket["run"], "attempt": ticket["attempt"], "stage": ticket["request"]["stage_id"]})

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
