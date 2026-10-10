import time
import uuid
import unittest
from fastapi.testclient import TestClient
from cloud.app import app
from cloud.db import Base, engine
from cloud import desktop

class DesktopApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(engine)

    def account(self):
        client = TestClient(app)
        email = "pc-" + uuid.uuid4().hex + "@example.test"
        response = client.post("/api/register", json={
            "email": email, "password": "correct-long-password-1234"})
        self.assertEqual(response.status_code, 200)
        return client

    def test_ingestion_dedupe_tenant_isolation_and_revoke(self):
        owner, stranger = self.account(), self.account()
        pair = owner.post("/api/mobile/devices", json={"label": "Windows laptop"}).json()
        headers = {"Authorization": "Bearer " + pair["token"]}
        start = int(time.time() * 1000) - 80000
        body = {"events": [
            {"start_ms": start, "end_ms": start + 60000,
             "kind": "app", "identifier": "Code", "seconds": 32},
            {"start_ms": start, "end_ms": start + 60000,
             "kind": "git", "identifier": "gep-agent-os", "seconds": 0,
             "detail": "branch:main clean:false"}]}
        self.assertEqual(owner.post("/api/desktop/events", json=body).status_code, 401)
        self.assertEqual(owner.post("/api/desktop/events", json=body, headers=headers).json()["accepted"], 2)
        self.assertEqual(owner.post("/api/desktop/events", json=body, headers=headers).json()["duplicates"], 2)
        self.assertEqual(stranger.get("/api/desktop/summary").json()["apps"], [])
        self.assertEqual(owner.get("/api/desktop/summary").json()["apps"][0]["seconds"], 32)
        self.assertEqual(stranger.delete("/api/mobile/devices/" + pair["id"]).status_code, 404)
        owner.delete("/api/mobile/devices/" + pair["id"])
        self.assertEqual(owner.post("/api/desktop/events", json=body, headers=headers).status_code, 401)
        self.assertEqual(owner.delete("/api/desktop/events").status_code, 200)
        self.assertEqual(owner.get("/api/desktop/summary").json()["apps"], [])

    def test_invalid_time_and_long_identity(self):
        owner = self.account()
        token = owner.post("/api/mobile/devices", json={"label": "PC"}).json()["token"]
        timestamp = int(time.time()*1000) - 5000
        body = {"events": [{"start_ms": timestamp, "end_ms": timestamp+1000,
                 "kind": "app", "identifier": "A", "seconds": 7}]}
        self.assertEqual(owner.post("/api/desktop/events", json=body,
                         headers={"Authorization": "Bearer "+token}).status_code, 422)
