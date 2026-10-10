import tempfile,unittest
from pathlib import Path
from gep.demo import seed
from gep.engine import WorkflowEngine
class DemoTests(unittest.TestCase):
 def test_demo_seed(self):
  with tempfile.TemporaryDirectory() as tmp:
   db=str(Path(tmp)/"demo.db")
   result=seed(db)
   self.assertEqual(len(result["goals"]),3)
   state=WorkflowEngine(db).snapshot()
   self.assertEqual(len(state["steps"]),2)
   self.assertTrue(all(s["state"]=="pending" for s in state["steps"]))
   with self.assertRaises(ValueError):seed(db)
