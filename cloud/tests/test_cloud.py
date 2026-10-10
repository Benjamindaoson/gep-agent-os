import os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient

from cloud.db import Base,engine,Session
from cloud.app import app

class CloudTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  Base.metadata.create_all(engine)
  cls.client=TestClient(app)
  cls.client.__enter__()
 @classmethod
 def tearDownClass(cls):
  cls.client.__exit__(None,None,None)
 def register(self):
  import uuid
  email="person-"+uuid.uuid4().hex[:14]+"@example.test"
  c=TestClient(app)
  c.post("/api/register",json={"email":email,"password":"Very-long-password-123"})
  return c
 def test_unauthenticated_denied(self):
  self.assertEqual(self.client.get("/api/state").status_code,401)
 def test_goal_isolation(self):
  a=self.register();b=self.register()
  gid=a.post("/api/goals",json={"name":"career","domain":"career"}).json()["id"]
  self.assertEqual(len(a.get("/api/state").json()["goals"]),1)
  self.assertEqual(b.get("/api/state").json()["goals"],[])
  self.assertEqual(b.post("/api/projects",json={"name":"x","goal_id":gid}).status_code,404)
 def test_evidence_gate(self):
  c=self.register();g=c.post("/api/goals",json={"name":"learn"}).json()["id"]
  p=c.post("/api/projects",json={"name":"experiment","goal_id":g}).json()["id"]
  self.assertEqual(c.patch("/api/projects/"+p,json={"state":"shipped"}).status_code,409)
  task=c.post("/api/tasks",json={"title":"baseline","project_id":p}).json()["id"]
  self.assertEqual(c.post("/api/tasks/"+task+"/accept",json={}).status_code,409)
  self.assertEqual(c.post("/api/tasks/"+task+"/evidence",json={"uri":"artifact.json"}).status_code,200)
  self.assertEqual(c.post("/api/tasks/"+task+"/accept",json={}).status_code,200)
  self.assertEqual(c.patch("/api/projects/"+p,json={"state":"shipped"}).status_code,200)
 def test_mission_state_cross_device(self):
  a=self.register();g=a.post("/api/goals",json={"name":"graduate"}).json()["id"]
  mid=a.post("/api/missions",json={"goal_id":g,"instruction":"Review my progress every week"}).json()["id"]
  self.assertEqual(a.post("/api/missions/"+mid+"/approve",json={}).json()["state"],"approved")
  self.assertEqual(a.post("/api/missions/"+mid+"/pause",json={}).json()["state"],"paused")
  self.assertEqual(a.post("/api/missions/"+mid+"/resume",json={}).json()["state"],"approved")
  self.assertGreaterEqual(len(a.get("/api/state").json()["events"]),4)
 def test_home(self):
  self.assertIn("Mission Control",self.client.get("/").text)
