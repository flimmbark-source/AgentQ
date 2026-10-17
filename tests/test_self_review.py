import sys
from pathlib import Path
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from self_review import summarize, verify, pending, improvement_prompt

class SelfReviewTests(unittest.TestCase):
    def test_dry_run_does_not_claim_improvement(self):
        r=summarize("AQ-001",True,{"select":"success"},"")
        self.assertEqual(r["stage"],"dry_run")
        self.assertFalse(r["improvement_verified"])

    def test_success_requires_pr(self):
        r=summarize("AQ-001",False,{"select":"success","codex":"success","validate":"success","publish":"success"},"https://github.com/foo/bar/pull/2")
        self.assertEqual(r["stage"],"awaiting_review")
        self.assertFalse(r["improvement_verified"])

    def test_failed_validation_stays_failed(self):
        r=summarize("AQ-001",False,{"select":"success","codex":"success","validate":"failure"},"")
        self.assertEqual(r["stage"],"validation_failed")

    def test_prompt_refuses_failed_attempt(self):
        with self.assertRaises(ValueError):
            improvement_prompt({"schema_version":1,"stage":"validation_failed"})

    def test_open_improvement_blocks_another(self):
        self.assertTrue(pending([{"state":"open","body":"AgentQ Improvement For Run: 123"}]))
        self.assertFalse(pending([{"state":"closed","body":"AgentQ Improvement For Run: 123"}]))

    def test_guard_rejects_protected(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertRaises(ValueError,verify,Path(d),[".github/workflows/agentq.yml"])

    def test_guard_requires_regression_test(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"scripts").mkdir()
            (root/"scripts/select_task.py").write_text("x=1")
            with self.assertRaisesRegex(ValueError,"regression"):
                verify(root,["scripts/select_task.py"])
            (root/"tests").mkdir()
            (root/"tests/test_fix.py").write_text("import unittest")
            self.assertEqual(len(verify(root,["scripts/select_task.py","tests/test_fix.py"])),2)

    def test_no_change_is_no_improvement(self):
        self.assertEqual(verify(Path("."),[]),[])

if __name__=="__main__":
    unittest.main()
