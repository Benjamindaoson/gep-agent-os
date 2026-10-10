import unittest,uuid
from cloud.db import Base,engine,Session
from cloud.models import User,Goal,Mission
from cloud.worker import run_once
class WorkerTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):Base.metadata.create_all(engine)
 def test_worker_generates_draft_without_claiming_task_execution(self):
  uid=uuid.uuid4().hex
  with Session() as db:
   u=User(email="worker-"+uid+"@example.test",password_hash="test")
   db.add(u);db.flush()
   g=Goal(user_id=u.id,name="Study robotics",domain="learning")
   db.add(g);db.flush()
   m=Mission(user_id=u.id,goal_id=g.id,instruction="Make a plan",state="approved",approval=True)
   db.add(m);db.commit();mission_id=m.id
  # Other CI tests may have approved missions; deterministic test only checks
  # mock planner call and eventual state of the claimed mission.
  result=run_once(lambda id:"An evidence-based plan, to be reviewed.")
  self.assertTrue(result["claimed"])
  with Session() as db:
   claimed=db.get(Mission,result["mission_id"])
   self.assertEqual(claimed.state,"draft_ready")
   self.assertIn("reviewed",claimed.progress)
