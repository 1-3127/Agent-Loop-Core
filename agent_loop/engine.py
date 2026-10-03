"""Sequential workflow control with independent review and bounded restart."""

from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
import copy
import re

from .host import CapabilityRequest
from .storage import atomic_json, consume_once, digest, get_artifact, put_artifact, read_json


class LoopError(RuntimeError):
    pass


class UncertainCall(LoopError):
    pass


IN_FLIGHT = {"FRONTIER_IN_FLIGHT", "WORKER_IN_FLIGHT", "REVIEW_IN_FLIGHT"}
TERMINAL = {"DELIVERED", "FAILED", "ABORT"}
SAFE_EFFECTS = {"workspace_read", "workspace_write", "local_execute", "network_read", "sandbox_install"}


def validate_workflow(workflow, skills, initial_type):
    if not isinstance(workflow, dict) or not workflow.get("stages") or not workflow.get("goal_kind"):
        raise LoopError("workflow requires goal_kind and stages")
    previous = initial_type
    names = set()
    for stage in workflow["stages"]:
        sid = stage.get("id")
        skill = skills.get(stage.get("skill_id"))
        if not sid or sid in names or not skill or not stage.get("criteria") or not stage.get("capability"):
            raise LoopError("invalid stage or unknown skill")
        names.add(sid)
        if previous != skill["input_type"] or stage["capability"] != skill["capability"]:
            raise LoopError("skill type/capability mismatch")
        previous = skill["output_type"]


def workflow_key(specification, input_type):
    return digest({"goal_kind": specification["goal_kind"],
                   "requirements": specification.get("requirements", {}),
                   "criteria": specification.get("criteria", []),
                   "input_type": input_type})


class SessionEngine:
    """Adapters are injected; Core never creates a Host grant or invokes a tool directly."""

    def __init__(self, root: Path, ledger: Path, host, frontier, reviewer, workers: dict,
                 skills: dict, workflow_catalog: Path | None = None):
        if frontier is reviewer:
            raise LoopError("Reviewer must be independent of Frontier")
        self.root = Path(root)
        self.ledger = Path(ledger)
        self.host = host
        self.frontier = frontier
        self.reviewer = reviewer
        self.workers = workers
        self.skills = copy.deepcopy(skills)
        self.catalog_path = Path(workflow_catalog) if workflow_catalog else self.root / "catalog.json"
        for key, skill in self.skills.items():
            if not all(skill.get(k) for k in ("id", "input_type", "output_type", "capability")):
                raise LoopError("invalid skill")
            if skill["id"] != key:
                raise LoopError("skill key mismatch")

    def _folder(self, session_id):
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", session_id):
            raise LoopError("invalid Session ID")
        return self.root / session_id

    def _load(self, session_id):
        return read_json(self._folder(session_id) / "state.json")

    def _save(self, state):
        atomic_json(self._folder(state["id"]) / "state.json", state)

    def inspect(self, session_id):
        state = self._load(session_id)
        view = copy.deepcopy(state)
        if view["phase"] in IN_FLIGHT:
            view["status"] = "BLOCKED_UNCERTAIN"
        return view

    def start(self, grant, request: str, initial_data: bytes, initial_type: str,
              specification: dict | None, budget: dict):
        folder = self._folder(grant.session_id)
        if folder.exists():
            raise LoopError("Session namespace already exists")
        try:
            expiration = datetime.fromisoformat(grant.expires_at)
            valid_time = datetime.now(timezone.utc) < expiration <= datetime.now(timezone.utc) + timedelta(hours=1)
        except (ValueError, TypeError):
            valid_time = False
        if (not grant.host_id or not grant.ingress_id or not grant.receipt_sha256 or
            grant.request_sha256 != sha256(request.encode()).hexdigest() or
            grant.mode not in {"ACTUAL", "SYNTHETIC"} or not valid_time):
            raise LoopError("invalid Host start attestation")
        if any(not isinstance(budget.get(k), int) or budget[k] < 1
               for k in ("max_attempts", "max_reviews", "max_frontier_calls")):
            raise LoopError("invalid budget")
        if specification is not None and (not specification.get("ready") or not specification.get("goal_kind")):
            raise LoopError("specification not ready")
        # Burn before namespace creation. A crash after this point never refunds authority.
        consume_once(self.ledger, grant, grant.request_sha256)
        folder.mkdir(parents=True, exist_ok=False)
        input_ref = put_artifact(folder / "artifacts", initial_data, initial_type, "USER_INPUT")
        state = {"id": grant.session_id, "mode": grant.mode, "host_id": grant.host_id,
                 "ingress_id": grant.ingress_id, "receipt_sha256": grant.receipt_sha256,
                 "request": request, "specification": specification, "budget": budget,
                 "usage": {"attempts": 0, "reviews": 0, "frontier_calls": 0},
                 "input": input_ref, "workflow": None, "run": 0, "stage": 0,
                 "checkpoints": [], "candidate_skills": {}, "failure": None, "review": None, "decision": None,
                 "phase": "IDLE" if specification else "WAITING_FOR_CLARIFICATION",
                 "status": "ACTIVE", "history": [{"event": "SESSION_STARTED"}]}
        self._save(state)
        return self.inspect(grant.session_id)

    def provide_user_input(self, session_id, specification: dict):
        state = self._load(session_id)
        if state["phase"] != "WAITING_FOR_CLARIFICATION" or state["status"] != "ACTIVE":
            raise LoopError("not awaiting clarification")
        if not specification.get("ready") or not specification.get("goal_kind"):
            raise LoopError("specification not ready")
        state["specification"] = copy.deepcopy(specification)
        state["phase"] = "IDLE"
        state["history"].append({"event": "SPECIFICATION_FROZEN"})
        self._save(state)
        return self.inspect(session_id)

    def _catalog(self):
        return read_json(self.catalog_path) if self.catalog_path.exists() else {"workflows": {}, "skills": {}}

    def _skills(self, state):
        return {**self.skills, **self._catalog()["skills"], **state.get("candidate_skills", {})}

    def _add_candidates(self, state, candidates):
        for skill in candidates:
            if (not isinstance(skill, dict) or skill.get("status") != "candidate" or
                not all(skill.get(k) for k in ("id", "input_type", "output_type", "capability")) or
                skill["id"] in self._skills(state)):
                raise LoopError("invalid or duplicate candidate Skill")
            state["candidate_skills"][skill["id"]] = skill

    def _select_workflow(self, state):
        catalog = self._catalog()
        goal = state["specification"]["goal_kind"]
        matching = catalog["workflows"].get(workflow_key(state["specification"], state["input"]["type"]))
        if matching and matching.get("input_type") == state["input"]["type"]:
            workflow = matching["workflow"]
            state["history"].append({"event": "WORKFLOW_REUSED", "digest": digest(workflow)})
        else:
            self._charge(state, "frontier_calls", "FRONTIER_IN_FLIGHT")
            proposal = self.frontier.plan(copy.deepcopy(state["specification"]),
                                          copy.deepcopy(self._skills(state)), state["input"]["type"])
            if "workflow" in proposal:
                self._add_candidates(state, proposal.get("candidate_skills", []))
                workflow = proposal["workflow"]
            else:
                workflow = proposal
        if workflow["goal_kind"] != goal:
            raise LoopError("workflow goal mismatch")
        validate_workflow(workflow, self._skills(state), state["input"]["type"])
        state["workflow"] = workflow
        state["run"] += 1
        state["phase"] = "IDLE"
        state["history"].append({"event": "WORKFLOW_SELECTED", "run": state["run"], "digest": digest(workflow)})
        self._save(state)

    def _charge(self, state, key, phase):
        maximum = state["budget"]["max_" + key]
        if state["usage"][key] >= maximum:
            state["status"] = "ABORT"
            state["phase"] = "TERMINAL"
            state["history"].append({"event": "BUDGET_EXHAUSTED", "counter": key})
            self._save(state)
            raise StopIteration
        state["usage"][key] += 1
        state["phase"] = phase
        self._save(state)

    def _checkpoint_input(self, state):
        index = state["stage"]
        if index:
            self._validate_checkpoint(state, index - 1)
        ref = state["input"] if index == 0 else state["checkpoints"][index - 1]["artifact"]
        get_artifact(self._folder(state["id"]) / "artifacts", ref)
        return ref

    def _validate_checkpoint(self, state, index):
        entry = state["checkpoints"][index]
        previous = state["input"] if index == 0 else state["checkpoints"][index - 1]["artifact"]
        artifact = entry["artifact"]
        review = entry["review"]
        if (entry["stage"] != state["workflow"]["stages"][index]["id"] or
            entry["stage_digest"] != digest(state["workflow"]["stages"][index]) or
            entry["input_sha256"] != previous["sha256"] or
            artifact["source"] != previous["sha256"] or
            review["verdict"] != "PASS" or review["artifact_sha256"] != artifact["sha256"] or
            entry["decision"]["review_sha256"] != digest(review)):
            raise LoopError("checkpoint lineage/review mismatch")
        get_artifact(self._folder(state["id"]) / "artifacts", artifact)

    def _promote(self, state, skill_id):
        skill = self._skills(state)[skill_id]
        if skill.get("status") != "candidate" or state["mode"] != "ACTUAL":
            return
        catalog = self._catalog()
        catalog["skills"][skill_id] = {**skill, "status": "reusable"}
        atomic_json(self.catalog_path, catalog)
        state["candidate_skills"].pop(skill_id, None)

    def _remember_workflow(self, state):
        if state["mode"] != "ACTUAL":
            return
        catalog = self._catalog()
        catalog["workflows"][workflow_key(state["specification"], state["input"]["type"])] = {
            "input_type": state["input"]["type"], "workflow": state["workflow"],
            "verified_output": state["checkpoints"][-1]["artifact"]["sha256"]}
        atomic_json(self.catalog_path, catalog)

    def _restart(self, state, target, new_workflow=None):
        current = state["workflow"]
        workflow = new_workflow or current
        validate_workflow(workflow, self._skills(state), state["input"]["type"])
        if workflow["goal_kind"] != state["specification"]["goal_kind"]:
            raise LoopError("workflow goal mismatch")
        ids = [stage["id"] for stage in workflow["stages"]]
        if target not in ids:
            raise LoopError("unknown restart stage")
        index = ids.index(target)
        if index > state["stage"]:
            raise LoopError("cannot restart downstream")
        for i in range(index):
            if i >= len(state["checkpoints"]) or current["stages"][i] != workflow["stages"][i]:
                raise LoopError("upstream workflow changed")
            self._validate_checkpoint(state, i)
        state["checkpoints"] = state["checkpoints"][:index]
        state["workflow"] = workflow
        state["stage"] = index
        if new_workflow is not None:
            state["run"] += 1
        state["history"].append({"event": "RESTART", "stage": target, "run": state["run"]})

    def _attempt(self, state):
        stage = state["workflow"]["stages"][state["stage"]]
        skill = self._skills(state)[stage["skill_id"]]
        input_ref = self._checkpoint_input(state)
        worker = self.workers.get(stage["capability"])
        if worker is None:
            raise LoopError("no Worker capability")
        effects = tuple(worker.effects)
        paths = tuple(worker.paths(self._folder(state["id"])))
        if not set(effects) <= SAFE_EFFECTS or not self.host.authorize(CapabilityRequest(stage["capability"], effects, paths)):
            state["status"] = "ABORT"
            state["phase"] = "TERMINAL"
            state["history"].append({"event": "CAPABILITY_DENIED", "capability": stage["capability"]})
            self._save(state)
            return
        self._charge(state, "attempts", "WORKER_IN_FLIGHT")
        input_bytes = get_artifact(self._folder(state["id"]) / "artifacts", input_ref)
        # Instruction is transient; no raw prompt is persisted.
        output = worker.execute(input_bytes, stage, state["specification"], state["review"])
        artifact = put_artifact(self._folder(state["id"]) / "artifacts", output, skill["output_type"], input_ref["sha256"])
        state["failure"] = {"stage": stage["id"], "artifact": artifact, "input_sha256": input_ref["sha256"]}
        state["phase"] = "REVIEW_PENDING"
        self._save(state)
        self._charge(state, "reviews", "REVIEW_IN_FLIGHT")
        judgment = self.reviewer.review(get_artifact(self._folder(state["id"]) / "artifacts", artifact),
                                        artifact, copy.deepcopy(stage["criteria"]), state["specification"])
        if judgment.get("verdict") not in {"PASS", "REVISE"} or not judgment.get("reason"):
            raise LoopError("invalid independent Review")
        state["review"] = {**judgment, "artifact_sha256": artifact["sha256"],
                           "stage": stage["id"], "criteria": stage["criteria"]}
        state["phase"] = "DECISION_PENDING"
        self._save(state)
        self._charge(state, "frontier_calls", "FRONTIER_IN_FLIGHT")
        decision = self.frontier.decide(copy.deepcopy(state["specification"]), copy.deepcopy(state["workflow"]),
                                         copy.deepcopy(state["review"]), copy.deepcopy(state["checkpoints"]),
                                         state["stage"])
        action = decision.get("action")
        if not decision.get("reason"):
            raise LoopError("Frontier Decision needs a reason")
        if action in {"CONTINUE", "ACCEPT"}:
            if judgment["verdict"] != "PASS":
                raise LoopError("cannot accept a failed Review")
            if (action == "ACCEPT") != (state["stage"] == len(state["workflow"]["stages"]) - 1):
                raise LoopError("invalid completion boundary")
        if action == "RETRY" and judgment["verdict"] != "REVISE":
            raise LoopError("retry needs a failed Review")
        if action == "REWORKFLOW" and not decision.get("workflow"):
            raise LoopError("reworkflow requires a Workflow")
        if action == "REWORKFLOW":
            self._add_candidates(state, decision.get("candidate_skills", []))
        state["decision"] = {**decision, "review_sha256": digest(state["review"])}
        if action in {"CONTINUE", "ACCEPT"}:
            state["checkpoints"].append({"stage": stage["id"], "artifact": artifact,
                                          "stage_digest": digest(stage), "input_sha256": input_ref["sha256"],
                                          "review": copy.deepcopy(state["review"]),
                                          "decision": copy.deepcopy(state["decision"])})
            state["failure"] = None
            self._promote(state, stage["skill_id"])
            if action == "ACCEPT":
                state["status"] = "INTERNAL_ACCEPT"
                state["phase"] = "AWAITING_DELIVERY"
            else:
                state["stage"] += 1
                state["phase"] = "IDLE"
        elif action == "RETRY":
            state["phase"] = "IDLE"
        elif action in {"RESTART", "REWORKFLOW"}:
            self._restart(state, decision.get("stage"), decision.get("workflow") if action == "REWORKFLOW" else None)
            state["phase"] = "IDLE"
        elif action == "STOP":
            state["status"] = "FAILED"
            state["phase"] = "TERMINAL"
        else:
            raise LoopError("invalid Frontier decision")
        state["history"].append({"event": "DECISION", "action": action,
                                 "run": state["run"], "attempt": state["usage"]["attempts"]})
        self._save(state)
        self._prune(state)

    def deliver(self, session_id, artifact_sha256: str, host_receipt: str):
        """Host attests that it actually presented the accepted output to the User."""
        state = self._load(session_id)
        if (state["status"] != "INTERNAL_ACCEPT" or not host_receipt or
            not state["checkpoints"] or
            artifact_sha256 != state["checkpoints"][-1]["artifact"]["sha256"]):
            raise LoopError("missing exact accepted output or Host delivery receipt")
        self._validate_checkpoint(state, len(state["checkpoints"]) - 1)
        state["status"] = "DELIVERED"
        state["phase"] = "TERMINAL"
        state["history"].append({"event": "DELIVERED", "receipt": host_receipt})
        self._save(state)
        self._remember_workflow(state)
        return self.inspect(session_id)

    def _prune(self, state):
        keep = {state["input"]["sha256"]}
        keep.update(item["artifact"]["sha256"] for item in state["checkpoints"])
        if state["failure"]:
            keep.add(state["failure"]["artifact"]["sha256"])
        for path in (self._folder(state["id"]) / "artifacts").iterdir():
            if path.name not in keep:
                path.unlink()

    def resolve_uncertain(self, session_id, evidence: str):
        """Host records external reconciliation and closes an uncertain call.

        No retry is inferred from an incomplete Worker/Reviewer/Frontier invocation.
        """
        state = self._load(session_id)
        if state["phase"] not in IN_FLIGHT | {"REVIEW_PENDING", "DECISION_PENDING"} or not evidence:
            raise LoopError("no uncertain call or missing external evidence")
        state["status"] = "FAILED"
        state["phase"] = "TERMINAL"
        state["history"].append({"event": "UNCERTAIN_CLOSED", "evidence": evidence})
        self._save(state)

    def run(self, session_id, max_steps=None):
        state = self._load(session_id)
        if state["phase"] in IN_FLIGHT:
            raise UncertainCall("in-flight effect requires Host reconciliation")
        if state["status"] != "ACTIVE" or state["phase"] == "WAITING_FOR_CLARIFICATION":
            return self.inspect(session_id)
        if state["phase"] != "IDLE":
            raise UncertainCall("incomplete decision boundary requires reconciliation")
        try:
            if state["workflow"] is None:
                self._select_workflow(state)
            steps = 0
            while state["status"] == "ACTIVE" and (max_steps is None or steps < max_steps):
                self._attempt(state)
                steps += 1
        except StopIteration:
            pass
        return self.inspect(session_id)
