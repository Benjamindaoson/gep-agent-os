import tempfile
import unittest
from pathlib import Path

from gep.store import GEPStore


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = GEPStore(Path(self.temp.name) / "state.db")
        self.db.initialize()

    def test_project_requires_alignment_before_start(self):
        p = self.db.add_project("Unrelated side quest")
        with self.assertRaisesRegex(ValueError, "goal link"):
            self.db.decide_project(p, "active")
        self.db.decide_project(p, "active", override=True)
        self.assertEqual(self.db.handoff(p)["project"]["state"], "active")

    def test_wip_limit_and_goal_link(self):
        g = self.db.add_goal("career", "career")
        projects = [self.db.add_project(str(i), [g]) for i in range(3)]
        self.db.decide_project(projects[0], "active")
        self.db.decide_project(projects[1], "active")
        with self.assertRaisesRegex(ValueError, "WIP"):
            self.db.decide_project(projects[2], "active")

    def test_verified_evidence_is_required(self):
        goal = self.db.add_goal("complete program", "learning")
        project = self.db.add_project("course", [goal])
        task = self.db.add_task(project, "finish assessment")
        with self.assertRaisesRegex(ValueError, "verified evidence"):
            self.db.verify_task(task)
        self.db.add_evidence(task, "results/report.pdf", verified=False)
        with self.assertRaisesRegex(ValueError, "verified evidence"):
            self.db.verify_task(task)
        self.db.add_evidence(task, "results/grade.json", verified=True)
        self.db.verify_task(task)
        self.assertEqual(self.db.handoff(project)["next_actions"], [])

    def test_checkpoint_and_ship(self):
        goal = self.db.add_goal("health", "life")
        p = self.db.add_project("healthy routine", [goal])
        self.db.decide_project(p, "active")
        t = self.db.add_task(p, "log sustainable routine")
        with self.assertRaises(ValueError):
            self.db.decide_project(p, "shipped")
        self.db.add_resource(p, "storage", "local", "data/health.json")
        self.db.add_evidence(t, "notes/verified.json", verified=True)
        self.db.verify_task(t)
        self.db.decide_project(p, "shipped")
        self.assertEqual(self.db.handoff(p)["project"]["state"], "shipped")
        self.assertTrue(self.db.checkpoint(p).startswith("snapshot_"))


if __name__ == "__main__":
    unittest.main()
