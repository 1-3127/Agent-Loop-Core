import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from agent_loop import SessionEngine, SandboxHost, VerifiedStartGrant, LoopError, UncertainCall
from agent_loop.host import CapabilityRequest, CodexTranscriptHost


class Worker:
    effects = ("workspace_read", "workspace_write", "local_execute")

    def __init__(self, suffix, fail_first=False):
        self.suffix = suffix
        self.fail_first = fail_first
        self.calls = 0

    def paths(self, folder):
        return (str(folder),)

    def execute(self, data, stage, specification, review):
        self.calls += 1
        return data + (b"BAD" if self.fail_first and self.calls == 1 else self.suffix)


class Reviewer:
    def __init__(self):
        self.calls = 0

    def review(self, data, artifact, criteria, specification):
        self.calls += 1
        return {"verdict": "REVISE" if data.endswith(b"BAD") else "PASS",
                "reason": "bad suffix" if data.endswith(b"BAD") else "criterion met"}


class Frontier:
    def __init__(self, workflow):
        self.workflow = workflow
        self.plan_calls = 0
        self.decide_calls = 0

    def plan(self, specification, skills, initial_type):
        self.plan_calls += 1
        return self.workflow

    def decide(self, specification, workflow, review, checkpoints, index):
        self.decide_calls += 1
        if review["verdict"] == "REVISE":
            return {"action": "RESTART", "stage": workflow["stages"][index]["id"], "reason": "local correction"}
        return {"action": "ACCEPT" if index == len(workflow["stages"]) - 1 else "CONTINUE",
                "reason": "review passed"}


def workflow(goal="mesh", kind="image", middle="views", output="mesh"):
    return {"goal_kind": goal, "stages": [
        {"id": "prepare", "skill_id": "prepare", "capability": "make_middle", "criteria": ["valid middle"]},
        {"id": "finish", "skill_id": "finish", "capability": "make_output", "criteria": ["valid output"]}]}


def skills(kind="image", middle="views", output="mesh"):
    return {"prepare": {"id": "prepare", "input_type": kind, "output_type": middle,
                         "capability": "make_middle", "status": "candidate"},
            "finish": {"id": "finish", "input_type": middle, "output_type": output,
                       "capability": "make_output", "status": "candidate"}}


class LoopTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.host = SandboxHost(self.root, set(Worker.effects))
        self.w1, self.w2 = Worker(b"-views"), Worker(b"-mesh", fail_first=True)
        self.frontier = Frontier(workflow())
        self.reviewer = Reviewer()
        self.engine = self.make_engine()

    def make_engine(self, *, host=None, frontier=None, reviewer=None, workers=None, skill_map=None):
        return SessionEngine(self.root / "sessions", self.root / "stable-ledger", host or self.host,
                             frontier or self.frontier, reviewer or self.reviewer,
                             workers or {"make_middle": self.w1, "make_output": self.w2},
                             skill_map or skills(), self.root / "catalog.json")

    def grant(self, sid, request="Make an asset", ingress=None, mode="ACTUAL"):
        return VerifiedStartGrant("test-host", ingress or sid, sid, hashlib.sha256(request.encode()).hexdigest(),
                                  (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(), "receipt-sha", mode)

    def start(self, sid="s1", mode="ACTUAL"):
        return self.engine.start(self.grant(sid, mode=mode), "Make an asset", b"source", "image",
                                 {"ready": True, "goal_kind": "mesh"},
                                 {"max_attempts": 4, "max_reviews": 4, "max_frontier_calls": 5})

    def delivered(self, engine, sid, accepted):
        self.assertEqual(accepted["status"], "INTERNAL_ACCEPT")
        return engine.deliver(sid, accepted["checkpoints"][-1]["artifact"]["sha256"], "host-presented-output")

    def test_checkpoint_restart_reuse_and_no_new_user_start(self):
        self.start()
        state = self.engine.run("s1", max_steps=2)
        self.assertEqual(state["status"], "ACTIVE")
        self.assertEqual(state["stage"], 1)
        self.assertEqual(len(state["checkpoints"]), 1)
        self.assertEqual(self.w1.calls, 1)
        self.assertEqual(state["failure"]["stage"], "finish")
        accepted = self.engine.run("s1")
        self.assertEqual(accepted["status"], "INTERNAL_ACCEPT")
        self.assertEqual(json.loads((self.root / "catalog.json").read_text())["workflows"], {})
        final = self.delivered(self.engine, "s1", accepted)
        self.assertEqual(final["status"], "DELIVERED")
        self.assertEqual((self.w1.calls, self.w2.calls), (1, 2))
        self.assertEqual(final["usage"], {"attempts": 3, "reviews": 3, "frontier_calls": 4})
        self.assertEqual(final["checkpoints"][1]["input_sha256"], final["checkpoints"][0]["artifact"]["sha256"])
        self.assertEqual(self.engine.run("s1"), final)
        catalog = json.loads((self.root / "catalog.json").read_text())
        self.assertEqual(set(catalog["skills"]), {"prepare", "finish"})
        cheaper = Frontier(workflow())
        engine2 = self.make_engine(frontier=cheaper, workers={"make_middle": Worker(b"-alt"),
                                                              "make_output": Worker(b"-alt")})
        engine2.start(self.grant("s2"), "Make an asset", b"source", "image",
                      {"ready": True, "goal_kind": "mesh"},
                      {"max_attempts": 3, "max_reviews": 3, "max_frontier_calls": 3})
        self.assertEqual(self.delivered(engine2, "s2", engine2.run("s2"))["status"], "DELIVERED")
        self.assertEqual(cheaper.plan_calls, 0)

    def test_grant_consumed_once_across_session_ids(self):
        self.start()
        with self.assertRaises(FileExistsError):
            self.engine.start(self.grant("different", ingress="s1"), "Make an asset", b"source", "image",
                              {"ready": True, "goal_kind": "mesh"},
                              {"max_attempts": 2, "max_reviews": 2, "max_frontier_calls": 2})
        self.assertFalse((self.root / "sessions" / "different").exists())

    def test_clarification_same_session_without_execution(self):
        self.engine.start(self.grant("dialogue"), "Make an asset", b"source", "image", None,
                          {"max_attempts": 2, "max_reviews": 2, "max_frontier_calls": 3})
        self.assertEqual(self.engine.run("dialogue")["phase"], "WAITING_FOR_CLARIFICATION")
        self.assertEqual(self.w1.calls, 0)
        self.engine.provide_user_input("dialogue", {"ready": True, "goal_kind": "mesh"})
        self.assertEqual(self.engine.run("dialogue", max_steps=1)["stage"], 1)

    def test_budget_and_authorization_denial(self):
        denied = self.make_engine(host=SandboxHost(self.root, {"workspace_read"}))
        denied.start(self.grant("denied"), "Make an asset", b"source", "image",
                     {"ready": True, "goal_kind": "mesh"},
                     {"max_attempts": 2, "max_reviews": 2, "max_frontier_calls": 2})
        self.assertEqual(denied.run("denied")["status"], "ABORT")
        self.assertEqual(self.w1.calls, 0)
        self.assertFalse(self.host.authorize(CapabilityRequest("x", ("paid_api",), (str(self.root),))))
        self.assertFalse(self.host.authorize(CapabilityRequest("x", ("workspace_write",), ("/etc",))))
        self.engine.start(self.grant("budget"), "Make an asset", b"source", "image",
                          {"ready": True, "goal_kind": "mesh"},
                          {"max_attempts": 2, "max_reviews": 2, "max_frontier_calls": 3})
        self.assertEqual(self.engine.run("budget")["status"], "ABORT")
        self.assertEqual(self.engine.inspect("budget")["usage"]["attempts"], 2)

    def test_interrupted_effect_does_not_duplicate(self):
        class Exploding(Worker):
            def execute(self, *args):
                self.calls += 1
                raise RuntimeError("lost response after submission")

        worker = Exploding(b"")
        engine = self.make_engine(workers={"make_middle": worker, "make_output": self.w2})
        engine.start(self.grant("uncertain"), "Make an asset", b"source", "image",
                     {"ready": True, "goal_kind": "mesh"},
                     {"max_attempts": 2, "max_reviews": 2, "max_frontier_calls": 3})
        with self.assertRaises(RuntimeError):
            engine.run("uncertain")
        self.assertEqual(engine.inspect("uncertain")["status"], "BLOCKED_UNCERTAIN")
        with self.assertRaises(UncertainCall):
            engine.run("uncertain")
        self.assertEqual(worker.calls, 1)

    def test_second_domain_and_worker_substitution(self):
        stage_plan = workflow("scene", "text", "layout", "scene")
        first, second = Worker(b"-layout"), Worker(b"-scene")
        planner = Frontier(stage_plan)
        engine = self.make_engine(frontier=planner, workers={"make_middle": first, "make_output": second},
                                  skill_map=skills("text", "layout", "scene"))
        engine.start(self.grant("scene"), "Make an asset", b"scene request", "text",
                     {"ready": True, "goal_kind": "scene"},
                     {"max_attempts": 2, "max_reviews": 2, "max_frontier_calls": 3})
        self.assertEqual(self.delivered(engine, "scene", engine.run("scene"))["status"], "DELIVERED")
        self.assertEqual((first.calls, second.calls), (1, 1))

    def test_candidate_discovery_reworkflow_and_promotion(self):
        initial = workflow()
        replacement = workflow()
        replacement["stages"][1]["skill_id"] = "finish-v2"

        class Replanner(Frontier):
            def plan(self, specification, known, initial_type):
                self.plan_calls += 1
                return {"workflow": initial, "candidate_skills": [skills()["finish"]]}

            def decide(self, specification, current, review, checkpoints, index):
                if review["verdict"] == "REVISE":
                    return {"action": "REWORKFLOW", "stage": "finish", "workflow": replacement,
                            "candidate_skills": [{**skills()["finish"], "id": "finish-v2"}],
                            "reason": "switch skill after failed artifact"}
                return super().decide(specification, current, review, checkpoints, index)

        frontier = Replanner(initial)
        engine = self.make_engine(frontier=frontier, skill_map={"prepare": skills()["prepare"]})
        engine.start(self.grant("replan"), "Make an asset", b"source", "image",
                     {"ready": True, "goal_kind": "mesh", "requirements": {"variant": "replan"}},
                     {"max_attempts": 4, "max_reviews": 4, "max_frontier_calls": 5})
        state = self.delivered(engine, "replan", engine.run("replan"))
        self.assertEqual(state["status"], "DELIVERED")
        self.assertEqual(state["run"], 2)
        self.assertEqual(self.w1.calls, 1)
        self.assertIn("finish-v2", json.loads((self.root / "catalog.json").read_text())["skills"])
        self.assertNotIn("finish", json.loads((self.root / "catalog.json").read_text())["skills"])

    def test_checkpoint_hash_mismatch_blocks_downstream(self):
        self.start("tamper")
        state = self.engine.run("tamper", max_steps=1)
        ref = state["checkpoints"][0]["artifact"]
        (self.root / "sessions" / "tamper" / "artifacts" / ref["sha256"]).write_bytes(b"corrupt")
        with self.assertRaises(ValueError):
            self.engine.run("tamper")
        self.assertEqual(self.w2.calls, 0)

    def test_new_process_style_engine_resumes_from_checkpoint(self):
        self.start("resume")
        state = self.engine.run("resume", max_steps=1)
        self.assertEqual(state["stage"], 1)
        replacement_frontier = Frontier(workflow())
        resumed = self.make_engine(frontier=replacement_frontier)
        accepted = resumed.run("resume")
        self.assertEqual(self.delivered(resumed, "resume", accepted)["status"], "DELIVERED")
        self.assertEqual(self.w1.calls, 1)
        self.assertEqual(replacement_frontier.plan_calls, 0)

    def test_delivery_requires_exact_artifact_and_receipt(self):
        self.start("delivery")
        accepted = self.engine.run("delivery")
        with self.assertRaises(LoopError):
            self.engine.deliver("delivery", "0" * 64, "presented")
        with self.assertRaises(LoopError):
            self.engine.deliver("delivery", accepted["checkpoints"][-1]["artifact"]["sha256"], "")
        self.assertEqual(self.engine.inspect("delivery")["status"], "INTERNAL_ACCEPT")

    def test_synthetic_proof_never_promotes(self):
        self.start("synthetic", mode="SYNTHETIC")
        self.assertEqual(self.delivered(self.engine, "synthetic", self.engine.run("synthetic"))["status"], "DELIVERED")
        self.assertFalse((self.root / "catalog.json").exists())

    def test_codex_host_rejects_foreign_event(self):
        transcript_root = self.root / "runtime"
        transcript_root.mkdir()
        file = transcript_root / "rollout-thread-123.jsonl"
        meta = {"type": "session_meta", "payload": {"id": "thread-123"}}
        event = {"type": "response_item", "payload": {"type": "message", "role": "assistant",
                                                       "content": [{"type": "input_text", "text": "start"}]}}
        file.write_text(json.dumps(meta) + "\n" + json.dumps(event) + "\n")
        host = CodexTranscriptHost(self.root, set(), transcript_root)
        with self.assertRaises(ValueError):
            host.verify_start(file, 2, "start", "id", (datetime.now(timezone.utc) + timedelta(minutes=2)).isoformat(),
                              lambda _: True)

        event["payload"]["role"] = "user"
        file.write_text(json.dumps(meta) + "\n" + json.dumps(event) + "\n")
        grant = host.verify_start(file, 2, "start", "id",
                                  (datetime.now(timezone.utc) + timedelta(minutes=2)).isoformat(), lambda _: True)
        self.assertEqual(grant.session_id, "id")
        self.assertEqual(grant.request_sha256, hashlib.sha256(b"start").hexdigest())


if __name__ == "__main__":
    unittest.main()
