import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from gep.store import GEPStore
from gep.ledger import RunLedger
from gep.integrations import OpenClaw,OpenHands,IntegrationError

class IntegratedTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.db=str(Path(self.tmp.name)/"db.sqlite");s=GEPStore(self.db);s.initialize()
  g=s.add_goal("learning","learning");p=s.add_project("project",[g])
  s.decide_project(p,"active");self.task=s.add_task(p,"step")
  self.ledger=RunLedger(self.db)
 def test_approval(self):
  with self.assertRaises(ValueError):self.ledger.launch(self.task,"openclaw","x",self.tmp.name)
 def test_provider_report_not_verification(self):
  with patch.object(OpenClaw,"launch",return_value={"status":"reported_complete","session_id":"s","result":"done"}):
   r=self.ledger.launch(self.task,"openclaw","x",self.tmp.name,approved=True)
  self.assertEqual(r["status"],"reported_complete")
  with self.assertRaises(ValueError):GEPStore(self.db).verify_task(self.task)
 def test_openhands_resume(self):
  with patch.object(OpenHands,"launch",return_value={"status":"submitted","session_id":"00000000-0000-0000-0000-000000000001","result":""}):
   r=self.ledger.launch(self.task,"openhands","x",self.tmp.name,approved=True)
  with patch.object(OpenHands,"poll",return_value={"status":"reported_complete","result":"finished"}):
   self.assertEqual(self.ledger.poll(r["id"])["status"],"reported_complete")
 def test_uncertain_failure_not_retried(self):
  with patch.object(OpenClaw,"launch",side_effect=IntegrationError("offline")):
   with self.assertRaises(IntegrationError):self.ledger.launch(self.task,"openclaw","x",self.tmp.name,approved=True)
  self.assertEqual(self.ledger.list()[0]["status"],"needs_reconciliation")
