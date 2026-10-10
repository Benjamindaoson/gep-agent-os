import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from gep.service import ObservationJournal,worker_loop
from gep.store import GEPStore
class ServiceTests(unittest.TestCase):
 def test_activity_import_and_latest(self):
  with tempfile.TemporaryDirectory() as tmp:
   db=str(Path(tmp)/"db")
   with patch("gep.service.ActivityWatchReader.summary",return_value={
      "app_seconds":{"Code":123},"events":3,"window_hours":24}):
    j=ObservationJournal(db);j.import_local()
   row=j.latest()
   self.assertEqual(row["app_seconds"]["Code"],123)
 def test_daemon_single_tick(self):
  with tempfile.TemporaryDirectory() as tmp:
   result=worker_loop(str(Path(tmp)/"db"),once=True)
   self.assertFalse(result["processed"]["claimed"])
