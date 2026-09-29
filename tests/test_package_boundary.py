"""The refactored Core imports independently from the single src root."""

import ast
import os
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PackageBoundaryTests(unittest.TestCase):
    def test_core_has_no_scenario_import(self):
        for path in (ROOT / "src/core").glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
            imports += [alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names]
            self.assertFalse(any(name and (name == "scenario_a" or name.startswith("scenario_a."))
                                 for name in imports), path.name)

    def test_single_src_root_imports_core_and_active_scenario(self):
        script = ("import sys, core.worker_port, core.result_review_adapter, core.reviewer_auth; "
                  "assert not any(name == 'scenario_a' or name.startswith('scenario_a.') "
                  "for name in sys.modules); "
                  "import scenario_a.c1_delegate, scenario_a.c2_review, scenario_a.c3_review, "
                  "scenario_a.c3_revision, scenario_a.c4_bounded, scenario_a.comfy_worker_adapter, "
                  "scenario_a.c5_worker_swap")
        env = dict(os.environ, PYTHONPATH=str(ROOT / "src"), PYTHONDONTWRITEBYTECODE="1")
        proc = subprocess.run([sys.executable, "-c", script], cwd=ROOT, env=env,
                              capture_output=True, text=True, timeout=20)
        self.assertEqual(proc.returncode, 0, proc.stderr)


if __name__ == "__main__":
    unittest.main()
