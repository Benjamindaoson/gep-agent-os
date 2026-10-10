import tempfile,unittest
from pathlib import Path
from gep.store import GEPStore
from gep.dashboard import dashboard_data,render
class DashboardTests(unittest.TestCase):
 def test_render_contains_goal_and_project(self):
  with tempfile.TemporaryDirectory() as tmp:
   db=str(Path(tmp)/"db");s=GEPStore(db);s.initialize()
   g=s.add_goal("<goal>","learning");s.add_project("Research",[g])
   page=render(dashboard_data(db))
   self.assertIn("&lt;goal&gt;",page)
   self.assertIn("Research",page)
   self.assertIn("GEP Mission Control",page)
   self.assertNotIn("<goal>",page)
