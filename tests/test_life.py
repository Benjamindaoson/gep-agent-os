import tempfile,unittest
from pathlib import Path
from gep.store import GEPStore
from gep.life import LifePortfolio
class LifePortfolioTests(unittest.TestCase):
 def test_budget_and_protected_goals(self):
  with tempfile.TemporaryDirectory() as d:
   p=str(Path(d)/"db");s=GEPStore(p);s.initialize()
   a=s.add_goal("robotics career","career");b=s.add_goal("rest and sleep","life")
   life=LifePortfolio(p)
   life.plan(a,priority=1,weekly_hours=30)
   life.plan(b,priority=1,protected=True,weekly_hours=15)
   life.link(b,a,"supports")
   result=life.report(40)
   self.assertTrue(result["overcommitted"])
   self.assertIn("rest and sleep",result["protected_goals"])
   self.assertEqual(result["links"][0]["relation"],"supports")
 def test_bad_values(self):
  with tempfile.TemporaryDirectory() as d:
   p=str(Path(d)/"db");s=GEPStore(p);s.initialize();g=s.add_goal("g","life")
   life=LifePortfolio(p)
   with self.assertRaises(ValueError):life.plan(g,weekly_hours=200)
   with self.assertRaises(ValueError):life.link(g,g,"competes")
