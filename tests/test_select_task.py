import json
import sys
from pathlib import Path
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from select_task import read_queue, select, write_selection


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.tasks = read_queue(Path(__file__).parents[1] / "tasks" / "queue.json")

    def test_initial_selection(self):
        task, reason = select(self.tasks, [])
        self.assertEqual(task["id"], "AQ-001")

    def test_open_pr_moves_to_next(self):
        prs = [{"body": "AgentQ Task: AQ-001\n", "state": "open", "merged_at": None}]
        task, _ = select(self.tasks, prs)
        self.assertEqual(task["id"], "AQ-002")

    def test_merged_pr_prevents_repeat(self):
        prs = [{"body": "AgentQ Task: AQ-001\n", "state": "closed", "merged_at": "2026-10-17T09:00:00Z"}]
        task, _ = select(self.tasks, prs)
        self.assertEqual(task["id"], "AQ-002")

    def test_capacity_limit(self):
        prs = [{"body": f"AgentQ Task: AQ-{i:03d}", "state": "open", "merged_at": None} for i in (1, 2)]
        task, reason = select(self.tasks, prs, max_open=2)
        self.assertIsNone(task)
        self.assertIn("capacity limit", reason)

    def test_closed_unmerged_is_retryable(self):
        prs = [{"body": "AgentQ Task: AQ-001", "state": "closed", "merged_at": None}]
        task, _ = select(self.tasks, prs)
        self.assertEqual(task["id"], "AQ-001")

    def test_unknown_manual_task_raises(self):
        with self.assertRaises(ValueError):
            select(self.tasks, [], "AQ-999")

    def test_dependencies(self):
        tasks = json.loads(json.dumps(self.tasks))
        tasks[1]["dependencies"] = ["AQ-001"]
        prs = [{"body": "AgentQ Task: AQ-001", "state": "open", "merged_at": None}]
        task, _ = select(tasks, prs)
        self.assertEqual(task["id"], "AQ-003")

    def test_writes_prompt_and_selection(self):
        with tempfile.TemporaryDirectory() as folder:
            write_selection(folder, self.tasks[0], "selected")
            self.assertIn("has_task=true", (Path(folder) / "selection.env").read_text())
            self.assertIn("AQ-001", (Path(folder) / "prompt.md").read_text())
            self.assertEqual(json.loads((Path(folder) / "task.json").read_text())["id"], "AQ-001")


if __name__ == "__main__":
    unittest.main()
