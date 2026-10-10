import subprocess
import tempfile
import unittest
from pathlib import Path

from gep.git_context import inspect_repo


class GitContextTests(unittest.TestCase):
    def test_snapshot_tracks_commit_and_local_changes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            def git(*args):
                subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)
            git("init", "-q")
            git("config", "user.name", "GEP Test")
            git("config", "user.email", "gep-test@example.invalid")
            doc = root / "demo.txt"
            doc.write_text("v1\n")
            git("add", "demo.txt")
            git("commit", "-qm", "init")
            clean = inspect_repo(root)
            self.assertTrue(clean["clean"])
            self.assertEqual(len(clean["commit_sha"]), 40)
            doc.write_text("v2\n")
            dirty = inspect_repo(root)
            self.assertFalse(dirty["clean"])
            self.assertIn("demo.txt", dirty["changed_paths"])
            self.assertEqual(dirty["untracked_count"], 0)


if __name__ == "__main__":
    unittest.main()
