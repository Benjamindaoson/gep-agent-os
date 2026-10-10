import tempfile,subprocess,unittest
from pathlib import Path
from gep.workspace import create_snapshot,restore_snapshot
class WorkspaceTests(unittest.TestCase):
 def test_snapshot_restores_uncommitted_and_excludes_secrets(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/"code";root.mkdir()
   def git(*args):subprocess.run(["git","-C",str(root),*args],check=True,capture_output=True)
   git("init","-q");git("config","user.email","test@example.invalid");git("config","user.name","Tester")
   (root/"app.py").write_text("version=1")
   git("add","app.py");git("commit","-qm","initial")
   (root/"app.py").write_text("version=2")
   (root/"new.txt").write_text("untracked")
   (root/".env").write_text("PRIVATE_KEY=secret")
   archive=Path(tmp)/"backup.tar.gz"
   result=create_snapshot(root,archive)
   self.assertEqual(result["files"],2)
   dest=Path(tmp)/"restored"
   with self.assertRaises(ValueError):restore_snapshot(archive,dest)
   response=restore_snapshot(archive,dest,approved=True)
   self.assertEqual(response["restored_files"],2)
   self.assertEqual((dest/"app.py").read_text(),"version=2")
   self.assertFalse((dest/".env").exists())
   with self.assertRaises(ValueError):restore_snapshot(archive,dest,approved=True)
 def test_snapshot_must_be_external(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);subprocess.run(["git","-C",tmp,"init","-q"],check=True)
   with self.assertRaises(ValueError):create_snapshot(root,root/"snapshot.tar.gz")
