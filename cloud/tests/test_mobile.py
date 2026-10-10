import unittest,time,uuid
from fastapi.testclient import TestClient
from cloud.app import app
from cloud.db import Base,engine
from cloud import mobile  # registers table metadata
class MobileTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  Base.metadata.create_all(engine)
 def account(self):
  c=TestClient(app)
  email="android-"+uuid.uuid4().hex+"@example.test"
  self.assertEqual(c.post("/api/register",json={"email":email,"password":"test-password-1234"}).status_code,200)
  return c
 def test_token_separation_revocation_and_dedupe(self):
  a=self.account();b=self.account()
  result=a.post("/api/mobile/devices",json={"label":"My Pixel"}).json()
  token=result["token"];device=result["id"]
  start=int(time.time()*1000)-120_000
  payload={"events":[{"start_ms":start,"end_ms":start+60_000,
    "package":"org.example.editor","foreground_ms":21_000}]}
  self.assertEqual(a.post("/api/mobile/usage",json=payload).status_code,401)
  headers={"Authorization":"Bearer "+token}
  self.assertEqual(a.post("/api/mobile/usage",json=payload,headers=headers).json()["accepted"],1)
  self.assertEqual(a.post("/api/mobile/usage",json=payload,headers=headers).json()["accepted"],0)
  self.assertEqual(b.get("/api/mobile/usage").json()["apps"],[])
  self.assertEqual(b.delete("/api/mobile/devices/"+device).status_code,404)
  self.assertEqual(a.delete("/api/mobile/devices/"+device).status_code,200)
  self.assertEqual(a.post("/api/mobile/usage",json=payload,headers=headers).status_code,401)
 def test_bad_measurements(self):
  a=self.account()
  token=a.post("/api/mobile/devices",json={"label":"Tablet"}).json()["token"]
  start=int(time.time()*1000)-60_000
  bad={"events":[{"start_ms":start,"end_ms":start+1000,
    "package":"com.example","foreground_ms":2000}]}
  self.assertEqual(a.post("/api/mobile/usage",json=bad,headers={
    "Authorization":"Bearer "+token}).status_code,422)
