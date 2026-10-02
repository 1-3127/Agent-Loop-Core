"""S3A fixture/local contract proof; no observed User delivery or host reset."""
import ast
import json
import sys
import tempfile
import unittest
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from session import session_boundary as s


class SessionBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.document = self.root / "specification.md"
        self.document.write_text(
            "# Fixture completed Specification\nsession_id: session-one\n"
            "version: v1\nNEW_WORK\nAC1: preserve silhouette\n"
            "authority: R1 fixture input\nEnvelope: technical choices only\n",
            encoding="utf-8")
        self.fields = s.FinalizedFields(
            "session-one", "v1", "NEW_WORK", True, (),
            (s.AcceptanceCriterion("AC1", "R1", True, "Preserve silhouette"),
             s.AcceptanceCriterion("AC2", "R1", False, "Optional polish")),
            (s.AuthorityReference("R1", "fixture://input-authority"),),
            ("Technical choices within fixed goal; criteria immutable",))
        self.boundary = s.SessionBoundary("session-one", self.root / "session", mode='SYNTHETIC')
        self.artifact = self.make_file("output.txt", "artifact-A", b"fixture output")
        self.review = self.make_file("review.json", "review-A", b'{"fixture":true,"verdict":"PASS"}')
        self.initial = self.make_file("input.txt", "input-A", b"fixture reference")
        self.ambiguity = s.SpecificationAmbiguity(
            "Goal has two incompatible interpretations", "Different output structures",
            "Current references do not establish the intended structure", ("Fruit", "Ship"))

    def make_file(self, name, identity, data):
        path = self.root / name
        path.write_bytes(data)
        return s.file_identity(path, identity)

    def freeze(self, **changes):
        return s.freeze_specification(self.document, replace(self.fields, **changes))

    def bind(self):
        frozen = self.freeze()
        return frozen, self.boundary.create_binding(frozen, "loop-one")

    def accept(self):
        frozen, binding = self.bind()
        accepted = self.boundary.internal_accept(binding, self.artifact, self.review, (self.initial,))
        return frozen, binding, accepted

    def package(self):
        frozen, binding, accepted = self.accept()
        package = self.boundary.prepare_delivery()
        receipt = s.SubmissionEvidence(
            package.sha256, frozen.reference.specification_sha256, self.artifact.sha256,
            "fixture-receipt-1", "fixture-user-channel", "2026-09-30T00:00:00+00:00",
            "fixture://external-host/observed-message-1")
        return frozen, binding, accepted, package, receipt

    def snapshot(self):
        return {p.name: p.read_bytes() for p in self.boundary.directory.iterdir() if p.is_file()}

    def test_t01_ready_specification_freeze_and_binding(self):
        frozen, binding = self.bind()
        self.assertEqual(frozen.reference.specification_sha256,
                         s.file_identity(self.document, "spec").sha256)
        self.assertEqual(binding.scenario, "scenario_a")
        self.assertEqual(binding.specification, frozen)
        self.assertEqual(self.boundary.outcome.status, "LOOP_READY")
        self.assertFalse(self.boundary.outcome.terminal)

    def test_t02_not_ready_cannot_create_execution_binding(self):
        frozen = self.freeze(specification_ready=False)
        with self.assertRaisesRegex(ValueError, "NOT_EXECUTION_ELIGIBLE"):
            self.boundary.create_binding(frozen, "loop-one")
        self.assertFalse((self.boundary.directory / "binding.json").exists())
        self.assertEqual(self.boundary.outcome.status, "REQUEST_RECEIVED")
        with self.assertRaisesRegex(ValueError, "NOT_EXECUTION_ELIGIBLE"):
            s.SessionRunBinding(frozen, "loop-one")

    def test_t03_blocking_ambiguity_prevents_binding_even_if_marked_ready(self):
        frozen = self.freeze(unresolved_blocking_ambiguities=(self.ambiguity,))
        with self.assertRaisesRegex(ValueError, "NOT_EXECUTION_ELIGIBLE"):
            self.boundary.create_binding(frozen, "loop-one")
        self.assertFalse((self.boundary.directory / "binding.json").exists())

    def test_t04_document_mutation_detected_on_reference_and_binding(self):
        frozen, binding = self.bind()
        self.document.write_bytes(b"changed document at identical path")
        for operation in (frozen.reference.validate, binding.validate):
            with self.assertRaisesRegex(ValueError, "CONTENT_CHANGED"):
                operation()
        with self.assertRaisesRegex(ValueError, "CONTENT_CHANGED"):
            self.boundary.internal_accept(binding, self.artifact, self.review)
        self.assertFalse((self.boundary.directory / "internal_accept.json").exists())

    def test_t05_session_and_loop_identity_are_separate(self):
        frozen, binding = self.bind()
        self.assertNotEqual(frozen.reference.session_id, binding.loop_run_id)
        with self.assertRaisesRegex(ValueError, "must differ"):
            s.SessionRunBinding(frozen, frozen.reference.session_id)
        with self.assertRaisesRegex(ValueError, "scenario_a"):
            s.SessionRunBinding(frozen, "loop-two", "another-scenario")

    def test_t06_duplicate_criterion_ids_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate criterion"):
            self.freeze(acceptance_criteria=(self.fields.acceptance_criteria[0],) * 2)

    def test_t07_missing_or_undeclared_criterion_authority_rejected(self):
        for authority in ("", "unknown-reference"):
            with self.subTest(authority=authority), self.assertRaises(ValueError):
                self.freeze(acceptance_criteria=(
                    replace(self.fields.acceptance_criteria[0], authority_ref=authority),))

    def test_t08_durable_context_is_explicit_selection_without_archive_loading(self):
        current = s.ContextRecord("CURRENT_REQUEST", "fixture://current-request")
        references = (s.ContextRecord("CURRENT_REFERENCE", "fixture://current-ref"),)
        durable = tuple(s.ContextRecord(category, "fixture://" + category) for category in sorted(
            s.STARTUP_CATEGORIES - {"CURRENT_REQUEST", "CURRENT_REFERENCE"}))
        payload = s.build_startup_context(current, references, durable)
        self.assertEqual(payload, (current,) + references + durable)
        self.assertTrue(any(r.category == "ARCHIVE_REFERENCE" for r in payload))
        self.assertFalse(hasattr(s, "FRESH_CONTEXT_VERIFIED"))

    def test_t09_transient_reasoning_and_unknown_categories_rejected(self):
        current = s.ContextRecord("CURRENT_REQUEST", "fixture://request")
        for category in ("CHAIN_OF_THOUGHT", "ACTIVE_REASONING_STATE", "THOUGHT_TRAJECTORY",
                         "RAW_SPECULATION", "HYPOTHESIS_CHRONOLOGY", "UNCLASSIFIED"):
            with self.subTest(category=category), self.assertRaisesRegex(ValueError, "not allowed"):
                s.build_startup_context(current, (), (s.ContextRecord(category, "fixture://ref"),))
        with self.assertRaises(ValueError):
            s.build_startup_context(current, (), (current,))

    def test_t10_internal_accept_is_not_delivery_and_pins_authority(self):
        frozen, binding, accepted = self.accept()
        state = self.boundary.outcome
        self.assertEqual(state.status, "INTERNAL_ACCEPT")
        self.assertFalse(state.delivered)
        self.assertFalse(state.terminal)
        data = json.loads(Path(accepted.path).read_text(encoding="utf-8"))
        self.assertEqual(data["binding_identity_sha256"], binding.identity_sha256)
        self.assertEqual(data["criterion_ids"], ["AC1", "AC2"])
        self.assertEqual(binding.specification.fields.acceptance_criteria,
                         self.fields.acceptance_criteria)
        with self.assertRaises(FrozenInstanceError):
            binding.specification.fields.acceptance_criteria[0].description = "Lower requirement"
        changed = replace(frozen, fields=replace(self.fields, acceptance_criteria=(
            replace(self.fields.acceptance_criteria[0], description="Different requirement"),)))
        self.assertNotEqual(changed.identity_sha256, frozen.identity_sha256)
        with self.assertRaisesRegex(ValueError, "ALREADY_INTERNAL_ACCEPTED"):
            self.boundary.create_binding(changed, "loop-two")
        self.assertEqual(self.boundary.outcome.status, "INTERNAL_ACCEPT")

    def test_t11_delivery_without_structured_submission_evidence_rejected(self):
        _, _, _, package, _ = self.package()
        for evidence in (None, True, {"submitted": True}):
            with self.subTest(evidence=evidence), self.assertRaises(ValueError):
                self.boundary.record_submission(package, evidence)
        for status in ("DELIVERED", "CLOSED"):
            with self.assertRaises(ValueError):
                self.boundary.stop(status, "self-declared")
        with self.assertRaises(TypeError):
            s.SessionOutcome(status="DELIVERED", terminal=True, delivered=True)
        self.assertFalse((self.boundary.directory / "terminal.json").exists())

    def test_t12_fixture_local_submission_contract_closes_without_user_approval(self):
        _, _, accepted, package, receipt = self.package()
        payload = json.loads(Path(package.path).read_text(encoding="utf-8"))
        self.assertEqual(payload["internal_accept"]["sha256"], accepted.sha256)
        self.assertEqual(payload["initial_references"], [s.asdict(self.initial)])
        terminal = self.boundary.record_submission(package, receipt)
        state = self.boundary.outcome
        self.assertEqual(state.status, "CLOSED")
        self.assertTrue(state.delivered)
        self.assertTrue(state.terminal)
        record = json.loads(Path(terminal.path).read_text(encoding="utf-8"))
        self.assertEqual(record["transitions"], ["DELIVERED", "CLOSED"])
        self.assertEqual(record["verification_scope"], "LOCAL_CALLER_SUPPLIED_EVIDENCE_CONTRACT_ONLY")
        self.assertNotIn("user_approval", record)
        terminal.validate()

    def test_t13_submission_package_artifact_and_specification_mismatch_rejected(self):
        _, _, _, package, receipt = self.package()
        for name in ("delivery_package_sha256", "artifact_sha256", "specification_sha256"):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "mismatch"):
                self.boundary.record_submission(package, replace(receipt, **{name: "0" * 64}))
        other_package = self.make_file("wrong-package.json", "wrong", Path(package.path).read_bytes())
        with self.assertRaisesRegex(ValueError, "package identity"):
            self.boundary.record_submission(other_package, receipt)
        self.assertFalse((self.boundary.directory / "terminal.json").exists())

    def test_t14_terminal_reentry_all_mutations_rejected_and_bytes_unchanged(self):
        frozen, binding, _, package, receipt = self.package()
        terminal = self.boundary.record_submission(package, receipt)
        before = self.snapshot()
        reopened_handle = s.SessionBoundary("session-one", self.boundary.directory, mode='SYNTHETIC')
        operations = (
            lambda: reopened_handle.create_binding(frozen, "loop-two"),
            lambda: reopened_handle.register_child_evidence("child", self.review),
            lambda: reopened_handle.internal_accept(binding, self.artifact, self.review),
            reopened_handle.prepare_delivery,
            lambda: reopened_handle.record_submission(package, receipt),
            lambda: reopened_handle.stop("ABORT", "try again"),
            lambda: reopened_handle.stop_for_ambiguity(frozen, self.ambiguity),
            reopened_handle.assert_open,
        )
        for operation in operations:
            with self.assertRaisesRegex(ValueError, "ALREADY_TERMINAL"):
                operation()
        terminal.validate()
        self.assertEqual(before, self.snapshot())

    def test_t15_typed_specification_ambiguity_is_session_terminal(self):
        frozen = self.freeze(specification_ready=False,
                             unresolved_blocking_ambiguities=(self.ambiguity,))
        terminal = self.boundary.stop_for_ambiguity(frozen, self.ambiguity)
        self.assertEqual(self.boundary.outcome.status, "BLOCKED_SPECIFICATION_AMBIGUITY")
        self.assertTrue(self.boundary.outcome.terminal)
        self.assertFalse(self.boundary.outcome.delivered)
        data = json.loads(Path(terminal.path).read_text(encoding="utf-8"))
        self.assertEqual(data["specification"], s.asdict(frozen.reference))
        self.assertEqual(data["ambiguity"]["alternatives"], ["Fruit", "Ship"])

    def test_t16_feedback_is_new_session_input_never_old_session_resume(self):
        _, _, _, package, receipt = self.package()
        terminal = self.boundary.record_submission(package, receipt)
        before = Path(terminal.path).read_bytes()
        feedback = s.ContextRecord("USER_FEEDBACK", "fixture://make-body-smoother")
        payload = s.build_startup_context(
            s.ContextRecord("CURRENT_REQUEST", "fixture://new-modification"), (), (feedback,))
        self.assertIn(feedback, payload)
        new_fields = replace(self.fields, session_id="session-two", request_type="ARTIFACT_MODIFICATION")
        new_document = self.root / "new-specification.md"
        new_document.write_text("# New fixture specification after dialogue", encoding="utf-8")
        frozen = s.freeze_specification(new_document, new_fields)
        with self.assertRaisesRegex(ValueError, "ALREADY_TERMINAL"):
            self.boundary.create_binding(frozen, "loop-two")
        new_session = s.SessionBoundary("session-two", self.root / "new-session", mode='SYNTHETIC')
        new_binding = new_session.create_binding(frozen, "loop-two")
        self.assertEqual(new_binding.specification.reference.session_id, "session-two")
        self.assertEqual(Path(terminal.path).read_bytes(), before)

    def test_invalid_projection_and_document_types_rejected(self):
        invalid_fields = (
            {"request_type": "UNSUPPORTED"}, {"specification_ready": "true"},
            {"session_id": ""}, {"specification_version": ""},
            {"acceptance_criteria": []}, {"interpretation_envelope": ()},
            {"unresolved_blocking_ambiguities": ("octree 128 vs 256 unknown",)},
            {"acceptance_criteria": (replace(self.fields.acceptance_criteria[0],
                                            blocking_when_unmet="false"),)},
        )
        for changes in invalid_fields:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.freeze(**changes)
        for path in (self.root, self.root / "missing.md"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                s.freeze_specification(path, self.fields)

    def test_typed_ambiguity_structure_and_no_technical_auto_classification(self):
        frozen = self.freeze()
        with self.assertRaisesRegex(ValueError, "typed"):
            self.boundary.stop_for_ambiguity(frozen, "octree 128 vs 256 unknown")
        for changes in ({"artifact_impact": ""}, {"context_insufficiency": ""},
                        {"alternatives": ("only one",)}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.boundary.stop_for_ambiguity(frozen, replace(self.ambiguity, **changes))
        self.assertFalse((self.boundary.directory / "terminal.json").exists())

    def test_write_once_binding_cannot_be_replaced_before_accept(self):
        frozen, _ = self.bind()
        before = self.snapshot()
        with self.assertRaises(FileExistsError):
            self.boundary.create_binding(frozen, "loop-two")
        self.assertEqual(before, self.snapshot())

    def test_artifact_review_and_package_mutation_rejected(self):
        for target in ("artifact", "review", "package"):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as directory:
                boundary = s.SessionBoundary("session-one", directory, mode='SYNTHETIC')
                frozen = self.freeze()
                binding = boundary.create_binding(frozen, "loop-one")
                artifact = self.make_file(target + "-output.txt", target, b"output")
                review = self.make_file(target + "-review.txt", target + "-review", b"review")
                boundary.internal_accept(binding, artifact, review)
                package = boundary.prepare_delivery()
                receipt = s.SubmissionEvidence(package.sha256, frozen.reference.specification_sha256,
                                               artifact.sha256, "fixture", "fixture", "2026-09-30T00:00:00Z",
                                               "fixture://receipt")
                identity = {"artifact": artifact, "review": review, "package": package}[target]
                Path(identity.path).write_bytes(b"mutated")
                with self.assertRaisesRegex(ValueError, "mismatch"):
                    boundary.record_submission(package, receipt)
                self.assertFalse((boundary.directory / "terminal.json").exists())

    def test_fail_abort_guards_and_premature_delivery_rejected(self):
        with self.assertRaises(FileNotFoundError):
            self.boundary.prepare_delivery()
        for status in ("FAILED", "ABORT"):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as directory:
                boundary = s.SessionBoundary("session-one", directory, mode='SYNTHETIC')
                terminal = boundary.stop(status, "Caller-defined stop policy")
                self.assertEqual(boundary.outcome.status, status)
                self.assertTrue(boundary.outcome.terminal)
                self.assertFalse(boundary.outcome.delivered)
                with self.assertRaisesRegex(ValueError, "ALREADY_TERMINAL"):
                    boundary.create_binding(self.freeze(), "loop-one")
                terminal.validate()

    def test_receipt_structure_namespace_and_timestamp_validation(self):
        _, _, _, package, receipt = self.package()
        for changes in ({"receipt_id": ""}, {"provenance_ref": ""}, {"observed_channel": ""},
                        {"observed_timestamp": "2026-09-30"}, {"observed_timestamp": "invalid"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.boundary.record_submission(package, replace(receipt, **changes))
        with self.assertRaisesRegex(ValueError, "directory identity"):
            s.SessionBoundary("session-other", self.boundary.directory, mode='SYNTHETIC')

    def test_session_module_has_no_execution_transport_or_core_scenario_import(self):
        tree = ast.parse((ROOT / "src/session/session_boundary.py").read_text(encoding="utf-8"))
        imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
        imports += [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
        prohibited = {"core", "scenario_a", "socket", "subprocess", "urllib", "requests"}
        self.assertFalse(any(name and name.split(".")[0] in prohibited for name in imports))


if __name__ == "__main__":
    unittest.main()
