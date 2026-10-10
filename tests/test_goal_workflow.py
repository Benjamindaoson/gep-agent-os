import tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from gep.store import GEPStore
from gep.workflow import run_goal_workflow
from gep.integrations import OpenClaw
class GoalWorkflowTests(unittest.TestCase):
 def test_goal_activity_and_execution_are_joined(self):
  with tempfile.TemporaryDirectory() as tmp:
   db=str(Path(tmp)/"db");s=GEPStore(db);s.initialize()
   goal=s.add_goal("finish thesis","learning")
   p=s.add_project("research project",[goal]);s.decide_project(p,"active")
   t=s.add_task(p,"reproduce result");prompts=[]
   def fake_run(self,prompt,workspace):
    prompts.append(prompt)
    return {"status":"reported_complete","session_id":"abc","result":"wrote report"}
   with patch.object(OpenClaw,"launch",fake_run),patch(
       "gep.workflow.ActivityWatchReader.summary",
       return_value={"app_seconds":{"Code":900.0}}):
    outcome=run_goal_workflow(db,t,"openclaw","review experiment",tmp,True,True)
   self.assertIn("finish thesis",prompts[0])
   self.assertIn('"Code": 900.0',prompts[0])
   self.assertTrue(outcome["activity_included"])
   self.assertEqual(outcome["run"]["status"],"reported_complete")
   with self.assertRaises(ValueError):s.verify_task(t)
 def test_no_approval_no_call(self):
  with self.assertRaises(ValueError):
   run_goal_workflow("unused","id","openhands","x",".",False)
