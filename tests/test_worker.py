import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from gep.store import GEPStore
from gep.engine import WorkflowEngine
from gep.runner import WorkflowWorker
from gep.integrations import OpenClaw,OpenHands
class WorkerTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.db=str(Path(self.temp.name)/"db");s=GEPStore(self.db);s.initialize()
  g=s.add_goal("learn","learning");p=s.add_project("build",[g]);s.decide_project(p,"active")
  self.engine=WorkflowEngine(self.db);w=self.engine.create(p,"w")
  self.step=self.engine.step(w,"step","openclaw","do it",self.temp.name,requires_approval=False)
  self.engine.start(w)
 def test_run_and_separate_verification(self):
  with patch.object(OpenClaw,"launch",return_value={
     "status":"reported_complete","session_id":"s","result":"done"}):
   result=WorkflowWorker(self.db).run_once()
  self.assertEqual(result["state"],"awaiting_verification")
  self.assertIsNone(self.engine.claim())
  a=self.engine.artifact(self.step,"log","artifact.txt")
  self.engine.verify(self.step,a,accepted=True)
  self.assertEqual(self.engine.snapshot()["steps"][0]["state"],"verified")
 def test_uncertain_errors_not_replayed(self):
  with patch.object(OpenClaw,"launch",side_effect=RuntimeError("uncertain")):
   result=WorkflowWorker(self.db).run_once()
  self.assertEqual(result["state"],"needs_reconciliation")
  self.assertFalse(WorkflowWorker(self.db).run_once()["claimed"])
