import json,tempfile,unittest
from pathlib import Path
from gep.resources import load_manifest,recovery_plan,file_digest
from gep.portfolio import review
from gep.store import GEPStore
class ResourceTests(unittest.TestCase):
 def test_manifest_and_digest(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/"m.json";f.write_text(json.dumps({"project":"A","resources":{
       "gpu":{"provider":"manual","persistent":False},"storage":{"provider":"s3","persistent":True}}}))
   self.assertEqual(len(recovery_plan(f)["resources"]),2)
   self.assertEqual(len(file_digest(f)),64)
   f.write_text(json.dumps({"resources":{"gpu":{"provider":"x","secret_key":"abc"}}}))
   with self.assertRaises(ValueError):load_manifest(f)
 def test_portfolio_review_is_not_fake_progress(self):
  with tempfile.TemporaryDirectory() as d:
   db=str(Path(d)/"db");s=GEPStore(db);s.initialize()
   g=s.add_goal("career","career");p=s.add_project("A",[g]);s.decide_project(p,"active")
   result=review(db,p)
   self.assertEqual(result["verified_evidence"],0)
   self.assertEqual(result["suggested_decision"],"review")
