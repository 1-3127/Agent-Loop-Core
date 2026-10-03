"""The Host composes concrete ports; the Core remains transport-independent."""
import json
import threading
from pathlib import Path

from .core import ContractError, Sessions, TERMINAL, check_ref, digest, file_ref, identity, require, write_once
from .host import LocalHost
from .models import CodexModel, safe_text
from .tools import Tools
from .promotion import Promotion


FRONTIER_INSTRUCTIONS = """Choose exactly one action; payload_json encodes its object.
Before freeze: ASK_USER {question}, or FREEZE {specification}. Interpret Request and original References.
Frozen specification fields: goal, deliverable_type, must_haves, should_haves, non_goals, constraints,
criteria [{id, description, mandatory:boolean, artifact_types:[type], evidence_slots:{slot:type}}],
Declare all required evidence slots, including diagnostics, before freeze. A multi-view criterion needs every view slot.
budget {frontier, reviewer, worker, diagnostic, runs, attempts, seconds}: positive finite integers.
Match User intent; do not invent extra deliverables or weaken mandatory criteria.
Never substitute a historical/demo Reference for a missing current User input; ask when required.
After freeze:
CREATE_SKILL {skill}: skill fields id, version, purpose, inputs, outputs, capabilities, dependencies,
subskills, known_failures, provenance, instructions. New knowledge is candidate, never fabricated validated.
PLAN {workflow, restart_from}: workflow fields version, stages, previous_hash, reason.
stage fields id, tool, skill:{id,version,hash}, inputs:{slot:type}, outputs:{slot:type}, parameters, local_parameters:[name].
Initial inputs reference-0 etc have type reference. Stage outputs use new slots. Initial version=1/previous_hash=null.
Revised version is run+1 with exact prior workflow hash. restart_from must name a stage and preceding stages must
remain identical with real checkpoints. A Workflow revision means new Run. Tool graphs are native Tool details.
EXECUTE {}: execute next current stage. RETRY {restart_from, local_parameters}: same strategy/new Attempt.
REVIEW {slots:[slot]}: supply every required slot of each applicable frozen criterion; partial coverage is rejected.
DIAGNOSE {tool, inputs:[slot], outputs:{slot:type}, parameters}: obtain more evidence, no strategy replacement.
RECONCILE {ticket_id}: observe an unresolved subordinate Tool; never blindly resubmit.
ACCEPT {}: only if all frozen mandatory criteria are MET in current independent reviews and final artifact reviewed.
PROMOTION {skill:{id,version,hash}, judgment}: record your task-specific reuse/promotion judgment with reason.
Consult compact promotion_history. No global ranking, frequency bias, unused penalty or automatic bulk promotion.
User praise of a Workflow or Artifact group does not endorse every participating Skill.
STOP {status:FAILED|ABORT|BLOCKED_SPECIFICATION_AMBIGUITY}: terminal; describe why. User ambiguity after freeze ends Session.
ESCALATE_HOST {request}: request Host policy/recovery/capability decision, not per-step User approval.
Always use reason for a concise evidence-backed rationale. Quality first, then resources. Only current lineage counts.
If evidence insufficient, request diagnosis/review rather than inventing success. Existing original Tool templates
and candidate skills are starting knowledge, not default mandatory workflow. At Session end retain authority,
final/undelivered output, checkpoints, failure evidence and reusable knowledge; cleanup suggestions are non-destructive.
"""


class Runtime:
    def __init__(self, config_path):
        self.config_path = Path(config_path).resolve()
        self.operation_lock = threading.RLock()
        self.config = json.loads(self.config_path.read_text(encoding="utf-8"))
        config = self.config
        self.host = LocalHost(config["host_inbox"], config["allowed_reads"], config["allowed_writes"])
        self.sessions = Sessions(config["state_root"], self.host.grant)
        self.promotion = Promotion(self.sessions.db)
        self.frontier = CodexModel("frontier", **config["frontier"])
        self.reviewer = CodexModel("reviewer", **config["reviewer"])
        self.tools = Tools(self.host, config["tools"])

    def bootstrap_knowledge(self):
        # No actual success is inherited from old proofs or templates.
        for path in self.config["skill_files"]:
            self.sessions.skill(json.loads(self.host.path(path).read_text(encoding="utf-8")))

    def status(self, sid):
        state = self.sessions.get(sid)
        if state["notice"]:
            notice = dict(state["notice"])
            delivered = self.promotion.delivered(sid)
            notice["undelivered_artifacts"] = [a for a in notice["undelivered_artifacts"] if a["id"] not in delivered]
            notice["user_delivery_observed"] = not notice["undelivered_artifacts"] and bool(delivered)
            if not notice["undelivered_artifacts"]:
                notice["required_host_action"] = None
                if state["status"] == "CLOSED" and notice["user_delivery_observed"]:
                    notice["abnormal_termination"] = False
            state["notice"] = notice
        application = state.get("application")
        recovery = None
        if state["status"] not in TERMINAL:
            if state["pending"]:
                recovery = {"owner": "HOST" if state["pending"]["role"] == "frontier" else "FRONTIER",
                            "reason": "Observe the original reserved invocation; never redispatch.", "host_escalation_allowed": True}
            elif application and application["phase"] in {"PREPARED", "APPLYING"}:
                recovery = {"owner": "HOST", "reason": "Frontier decision application interrupted.", "ticket_id": application["ticket_id"]}
            elif state["unresolved"]:
                recovery = {"owner": "FRONTIER", "reason": "Observe unresolved subordinate effects; upper model failures belong to Host.",
                            "host_escalation_allowed": True}
        return {"session_id": sid, "status": state["status"], "run": state["run"], "attempt": state["attempt"],
                "used": state["used"], "question": state.get("question"), "host_request": state.get("host_request"),
                "pending": state["pending"], "unresolved": state["unresolved"], "notice": state["notice"],
                "acceptance": state["acceptance"], "delivery": state["delivery"], "retention": state["retention"],
                "application": application, "recovery": recovery, "revision": state.get("revision", 0),
                "projection_error": state.get("projection_error")}

    def images(self, artifacts):
        # Media selection is Host-port detail, not Core type-specific dispatch.
        return [a["file"] for a in artifacts if Path(a["file"]["path"]).suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}]

    def visible(self, artifacts):
        from copy import deepcopy
        values = deepcopy(artifacts)
        for item in values:
            path = check_ref(item["file"])
            if path.suffix.lower() in {".json", ".txt", ".md"}:
                item["inline_excerpt"] = safe_text(path.read_bytes()[:65536])
                item["excerpt_is_complete"] = path.stat().st_size <= 65536
        return values

    def context(self, state):
        request = check_ref(state["grant"]["request"]).read_text(encoding="utf-8")
        require(len(request.encode("utf-8")) <= 65536, "REQUEST_CONTEXT_TOO_LARGE")
        current = [self.sessions.check_artifact(state, aid) for aid in state["slots"].values()]
        templates = [{"file": file_ref(self.host.path(p)), "metadata": json.loads(Path(p).read_text(encoding="utf-8"))}
                     for p in self.config["workflow_templates"]]
        return {"instructions": FRONTIER_INSTRUCTIONS, "request": request,
            "original_references": state["grant"]["references"], "dialogue_responses": [check_ref(r).read_text(encoding="utf-8") for r in state["dialogue"]],
            "frozen": state["spec"], "workflow": state["workflow"], "workflow_hash": digest(state["workflow"]),
            "run": state["run"], "attempt": state["attempt"], "cursor": state.get("cursor"),
            "used": state["used"], "artifacts": self.visible(current), "slots": state["slots"],
            "latest_reviews": self.sessions.current_reviews(state), "latest_decisions": state["decisions"][-3:],
            "current_failure": state.get("failure"), "unresolved": state["unresolved"],
            "skills": self.sessions.skills(), "promotion_history": self.promotion.catalog(self.sessions.skills()),
            "capabilities": self.tools.capabilities(), "tool_templates": templates}

    def advance(self, sid):
        with self.operation_lock:
            return self._advance(sid)

    def _advance(self, sid):
        state = self.sessions.get(sid)
        if state["status"] in TERMINAL or state["status"] == "ACCEPTED":
            return self.status(sid)
        if state["pending"] or state.get("question") or state.get("host_request") or (
                state.get("application") and state["application"]["phase"] in {"PREPARED", "APPLYING"}):
            return self.status(sid)
        context = self.context(state)
        try:
            ticket = self.sessions.reserve(sid, "frontier", {"context_hash": digest(context)})
        except ContractError as exc:
            if "BUDGET" in str(exc):
                self.sessions.close(sid, "ABORT", str(exc))
                return self.status(sid)
            raise
        images = self.images([state["artifacts"][aid] for aid in state["slots"].values()])
        if state["status"] == "DIALOGUE":
            images = [r for r in state["grant"]["references"] if Path(r["path"]).suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}]
        outcome = self.frontier(ticket, context, images)
        self.sessions.settle(sid, ticket, outcome)
        if outcome["status"] != "SUCCESS":
            return self.status(sid)
        decision = outcome["value"]
        try:
            self.apply(sid, decision)
        except (ContractError, KeyError, TypeError) as exc:
            # Once a reservation committed, only observation can resolve it.
            if self.sessions.get(sid)["application"]["phase"] != "PREPARED":
                raise
            self.sessions.reject(sid, str(exc))
            if "BUDGET" in str(exc):
                self.sessions.close(sid, "ABORT", str(exc))
        return self.status(sid)

    def apply(self, sid, decision):
        state = self.sessions.get(sid)
        require(state.get("application") and state["application"]["value"] == decision, "ORIGINAL_PREPARED_DECISION_REQUIRED")
        with self.sessions.application(sid, state["application"]["ticket_id"]):
            job = self.prepare_action(sid, decision)
        # Only now is the decision + effect ticket durable. No native effect
        # or model inference is allowed inside the Core application transaction.
        if job:
            kind, ticket, context, images = job
            if kind == "tool":
                outcome = self.tools.execute(ticket, context)
            else:
                outcome = self.reviewer(ticket, context, images)
                if outcome["status"] == "SUCCESS":
                    value = outcome["value"]
                    outcome["value"] = value["payload"] if value["action"] == "REVIEW" else {"invalid_action": value["action"]}
            self.sessions.settle(sid, ticket, outcome)

    def prepare_action(self, sid, decision):
        action, payload = decision["action"], decision["payload"]
        state = self.sessions.get(sid)
        if action == "ASK_USER":
            require(state["status"] == "DIALOGUE" and payload["question"], "QUESTION_AFTER_FREEZE")
            with self.sessions.edit(sid, "USER_INTENT_QUESTION") as current:
                current["question"] = payload["question"]
        elif action == "FREEZE":
            self.sessions.freeze(sid, payload["specification"])
        elif action == "CREATE_SKILL":
            self.sessions.skill(payload["skill"])
        elif action == "PLAN":
            for stage in payload["workflow"]["stages"]:
                require(stage["tool"] in self.tools.runners and set(stage["local_parameters"]) <= set(self.tools.local_tuning(stage["tool"], stage["parameters"])), "TOOL_LOCAL_TUNING_DECLARATION")
            self.sessions.workflow(sid, payload["workflow"], payload["restart_from"])
        elif action == "RETRY":
            self.sessions.workflow(sid, state["workflow"], payload["restart_from"], local=payload["local_parameters"])
        elif action in {"EXECUTE", "DIAGNOSE"}:
            return self.prepare_execute(sid, payload if action == "DIAGNOSE" else None)
        elif action == "REVIEW":
            return self.prepare_review(sid, payload["slots"])
        elif action == "RECONCILE":
            observed = state["unresolved"].get(payload["ticket_id"])
            require(observed and observed["ticket"]["role"] in {"worker", "diagnostic"}, "FRONTIER_RECOVERY_LAYER")
            result = self.tools.reconcile(observed["ticket"])
            self.sessions.recover(sid, payload["ticket_id"], result)
        elif action == "ACCEPT":
            self.sessions.accept(sid)
        elif action == "PROMOTION":
            self.sessions.promotion_decision(sid, payload, decision["reason"])
        elif action == "STOP":
            require(payload["status"] in {"FAILED", "ABORT", "BLOCKED_SPECIFICATION_AMBIGUITY"}, "FRONTIER_STOP_STATUS")
            self.sessions.close(sid, payload["status"], decision["reason"])
        elif action == "ESCALATE_HOST":
            with self.sessions.edit(sid, "HOST_DECISION_REQUESTED") as current:
                current["host_request"] = {"request": payload["request"], "reason": decision["reason"]}
        else:
            raise ContractError("UNKNOWN_FRONTIER_ACTION")

    def prepare_execute(self, sid, diagnostic=None):
        state = self.sessions.get(sid)
        require(state["status"] == "ACTIVE" and state["workflow"], "EXECUTION_REQUIRES_WORKFLOW")
        if diagnostic is None:
            require(state["cursor"] < len(state["workflow"]["stages"]), "WORKFLOW_ALREADY_COMPLETE")
            stage = state["workflow"]["stages"][state["cursor"]]
            parameters = dict(stage["parameters"])
            from copy import deepcopy
            parameters = deepcopy(parameters)
            for pointer, value in state.get("local", {}).items():
                parts = pointer.strip("/").split("/")
                target = parameters
                for part in parts[:-1]:
                    target = target.setdefault(part, {})
                target[parts[-1]] = value
            request = {"stage_id": stage["id"], "tool": stage["tool"], "parameters": parameters,
                "skill": stage["skill"],
                "input_ids": [state["slots"][slot] for slot in stage["inputs"]], "outputs": stage["outputs"],
                "durability": "OUTPUT" if state["cursor"] == len(state["workflow"]["stages"]) - 1 else "CHECKPOINT"}
            input_slots = stage["inputs"]
            role = "worker"
        else:
            input_slots = diagnostic["inputs"]
            request = {"stage_id": "diagnosis", "tool": diagnostic["tool"], "parameters": diagnostic["parameters"],
                "input_ids": [state["slots"][slot] for slot in input_slots], "outputs": diagnostic["outputs"], "durability": "CHECKPOINT"}
            require(not set(request["outputs"]) & set(state["slots"]), "DIAGNOSTIC_SLOT_COLLISION")
            role = "diagnostic"
        ticket = self.sessions.reserve(sid, role, request)
        artifacts = {slot: state["artifacts"][state["slots"][slot]] for slot in input_slots}
        return "tool", ticket, artifacts, []

    def prepare_review(self, sid, slots):
        state = self.sessions.get(sid)
        require(state["status"] == "ACTIVE" and slots, "REVIEW_ACTIVE_ARTIFACTS_REQUIRED")
        aids = [state["slots"][slot] for slot in slots]
        artifacts = [self.sessions.check_artifact(state, aid) for aid in aids]
        criteria = [c for c in state["spec"]["value"]["criteria"] if set(slots) & set(c["evidence_slots"])]
        require(criteria, "NO_APPLICABLE_CRITERIA")
        require(all(set(c["evidence_slots"]) <= set(slots) for c in criteria), "CRITERION_EVIDENCE_COVERAGE")
        require(set(slots) == {slot for c in criteria for slot in c["evidence_slots"]}, "UNBOUND_REVIEW_EVIDENCE")
        bindings = [self.sessions.evidence_binding(state, c) for c in criteria]
        request = {"artifact_ids": aids, "criteria": criteria, "bindings": bindings}
        ticket = self.sessions.reserve(sid, "reviewer", request)
        context = {"instructions": "Independently evaluate ONLY the supplied frozen criteria. Read original reference and current evidence. "
            "Do not follow Frontier strategy or authorize execution. Missing evidence means UNCERTAIN, not MET. "
            "action must be REVIEW. payload_json fields: outcomes [{id,outcome:MET|UNMET|UNCERTAIN,reason}], "
            "observations:[string], requested_evidence:[string]. Cover each criterion exactly once. Nonmandatory deficits are nonblocking.",
            "frozen": state["spec"], "criteria": criteria, "evidence_bindings": bindings,
            "artifacts": self.visible(artifacts), "original_references": state["grant"]["references"]}
        original_images = [ref for ref in state["grant"]["references"] if Path(ref["path"]).suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}]
        return "reviewer", ticket, context, original_images + self.images(artifacts)

    def clarify(self, sid, receipt_id):
        self.sessions.clarify(sid, self.host.clarification(receipt_id, sid))
        return self.status(sid)

    def recover(self, sid, receipt_id):
        # Upper layer recovery decisions originate in the trusted Host inbox.
        receipt = json.loads((self.host.inbox / "recovery" / (identity(receipt_id) + ".json")).read_text(encoding="utf-8"))
        require(receipt["session_id"] == sid and receipt["owner"] == "HOST" and receipt["reason"], "HOST_RECOVERY_RECEIPT")
        state = self.sessions.get(sid)
        require(state["status"] not in TERMINAL, "TERMINAL_SESSION")
        if receipt["action"] == "STOP":
            self.sessions.close(sid, "ABORT", receipt["reason"])
        elif receipt["action"] == "CLEAR_HOST_REQUEST":
            require(not state["pending"] and not state["unresolved"], "UNRESOLVED_RECOVERY")
            require(not state.get("application") or state["application"]["phase"] in {"APPLIED", "REJECTED"}, "INCOMPLETE_APPLICATION")
            with self.sessions.edit(sid, "HOST_REQUEST_RESOLVED") as current:
                current.pop("host_request", None)
        elif receipt["action"] in {"APPLY_DECISION", "REJECT_DECISION"}:
            application = state.get("application")
            require(application and application["ticket_id"] == receipt["ticket_id"] and
                    application["phase"] == "PREPARED" and not state["pending"], "EXACT_PREPARED_DECISION_REQUIRED")
            if receipt["action"] == "APPLY_DECISION":
                self.apply(sid, application["value"])
            else:
                self.sessions.reject(sid, receipt["reason"])
        elif receipt["action"] == "OBSERVE_TOOL":
            ticket = state["pending"] or state["unresolved"][receipt["ticket_id"]]["ticket"]
            require(ticket["id"] == receipt["ticket_id"], "EXACT_RECOVERY_TICKET_REQUIRED")
            ticket["directory"] = str(self.sessions.root / sid / "calls" / ticket["id"])
            require(ticket["role"] in {"worker", "diagnostic"}, "TOOL_RECOVERY_ROLE")
            self.sessions.recover(sid, ticket["id"], self.tools.reconcile(ticket))
        elif receipt["action"] == "OBSERVE_MODEL":
            ticket = state["pending"] or state["unresolved"][receipt["ticket_id"]]["ticket"]
            require(ticket["id"] == receipt["ticket_id"], "EXACT_RECOVERY_TICKET_REQUIRED")
            directory = self.sessions.root / sid / "calls" / ticket["id"]
            report_ref = file_ref(directory / "invocation.json")
            report = json.loads(check_ref(report_ref).read_text(encoding="utf-8"))
            require(report["ticket_id"] == ticket["id"] and report["role"] == ticket["role"] and report["status"] == "SUCCESS", "EXACT_MODEL_RESULT_REQUIRED")
            raw = json.loads(check_ref(report["result"]).read_text(encoding="utf-8"))
            value = {"action": raw["action"], "payload": json.loads(raw["payload_json"]), "reason": raw["reason"]}
            require(ticket["role"] != "reviewer" or value["action"] == "REVIEW", "REVIEW_ROLE_ACTION")
            result = {"status": "SUCCESS", "value": value["payload"] if ticket["role"] == "reviewer" else value, "report": report_ref}
            self.sessions.recover(sid, ticket["id"], result)
            with self.sessions.edit(sid, "HOST_RECOVERY_COMPLETE") as current:
                current.pop("host_request", None)
            if ticket["role"] == "frontier":
                self.apply(sid, value)
        else:
            raise ContractError("UNKNOWN_HOST_RECOVERY_ACTION")
        return self.status(sid)

    def assess(self, sid, receipt_id):
        item, ref = self.host.assessment(receipt_id, sid)
        self.sessions.assessment(sid, receipt_id, item, ref)
        return {"session": self.status(sid), "promotion": self.promotion.catalog(self.sessions.skills())}

    def deliver(self, sid, target):
        state = self.sessions.get(sid)
        try:
            receipt = self.host.deliver(state, target)
        except Exception:
            self.sessions.close(sid, "DELIVERY_FAILED", "Host delivery failed; preserve undelivered artifacts and notify User.")
            raise
        self.sessions.close(sid, "CLOSED", "Verified local handoff; human receipt and quality verdict unobserved.", receipt)
        return self.status(sid)

    def retention(self, sid, proposal, apply=False):
        self.sessions.retention(sid, proposal)
        state = self.sessions.get(sid)
        # Reversible quarantine, only files owned by this Session. Shared Tool
        # outputs/models and User originals are never cleanup targets.
        if apply:
            import shutil
            root = (self.sessions.root / sid).resolve()
            for aid in state["retention"]["prune"]:
                source = check_ref(state["artifacts"][aid]["file"])
                require(source.is_relative_to(root / "calls") and not source.is_symlink(), "CLEANUP_NOT_SESSION_OWNED")
            moved = []
            for aid in state["retention"]["prune"]:
                source = check_ref(state["artifacts"][aid]["file"])
                target = root / "retired" / aid / source.name
                require(not target.exists(), "RETIREMENT_NAMESPACE_COLLISION")
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source), str(target))
                moved.append({"source": str(source), "recoverable_at": str(target), "artifact_id": aid})
            write_once(root / "retention-result.json", {"session_id": sid, "moved": moved, "hard_deletions": 0})
        return self.status(sid)
