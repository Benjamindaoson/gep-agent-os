import tempfile,unittest
from pathlib import Path
from gep.store import GEPStore
from gep.engine import WorkflowEngine

class WorkflowTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.path=str(Path(self.tmp.name)/"state.sqlite")
  s=GEPStore(self.path);s.initialize()
  g=s.add_goal("Finish meaningful learning","learning")
  self.project=s.add_project("research",[g]);s.decide_project(self.project,"active")
  self.engine=WorkflowEngine(self.path)
 def test_approval_dependency_and_artifact_gates(self):
  w=self.engine.create(self.project,"training")
  first=self.engine.step(w,"baseline","openclaw","run baseline",self.tmp.name)
  second=self.engine.step(w,"summary","openhands","write report",self.tmp.name,[first],False)
  self.engine.start(w)
  self.assertIsNone(self.engine.claim())
  self.engine.approve(first)
  lease=self.engine.claim()
  self.assertEqual(lease["id"],first)
  self.engine.complete_execution(first,lease["lease_token"],"reported_complete")
  self.assertIsNone(self.engine.claim())
  artifact=self.engine.artifact(first,"report","report.json")
  with self.assertRaises(ValueError):self.engine.verify(first,artifact)
  self.engine.verify(first,artifact,accepted=True)
  self.assertEqual(self.engine.claim()["id"],second)
 def test_lease_reconciliation_guards(self):
  w=self.engine.create(self.project,"w");step=self.engine.step(w,"test","openclaw","x",self.tmp.name,requires_approval=False)
  self.engine.start(w)
  a=self.engine.claim()
  with self.assertRaises(ValueError):self.engine.complete_execution(step,"bad","reported_complete")
  self.engine.complete_execution(step,a["lease_token"],"needs_reconciliation")
  self.engine.reconcile(step,"pending")
  self.assertEqual(self.engine.claim()["attempt"],2)
  with self.assertRaises(ValueError):self.engine.reconcile(step,"pending")
 def test_snapshot_multiworkflows(self):
  a=self.engine.create(self.project,"A")
  b=self.engine.create(self.project,"B")
  self.engine.start(a);self.engine.start(b)
  self.assertEqual(len(self.engine.snapshot()["workflows"]),2)
