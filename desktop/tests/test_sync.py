import tempfile,unittest,os
from pathlib import Path
from unittest.mock import patch
from desktop.sync import sync_once,validate_server
class SyncTests(unittest.TestCase):
    def test_requires_https(self):
        with self.assertRaises(ValueError):validate_server("http://remote.example")
        self.assertEqual(validate_server("https://gep.example"),"https://gep.example")
    def test_cursor_advances_only_after_ack(self):
        conf={"server":"https://gep.example","git_paths":[],"last_sync_ms":0,"enabled":True}
        class Collector:
            def collect(self,start,end):
                return [{"start_ms":start,"end_ms":end,"kind":"app","identifier":"Code","seconds":30}]
        changed=[]
        with patch("desktop.sync.read_settings",return_value=conf),patch(
            "desktop.sync.get_token",return_value="gep_android_test"),patch(
            "desktop.sync.git_observations",return_value=[]),patch(
            "desktop.sync.save_settings",side_effect=lambda x:changed.append(dict(x))),patch(
            "desktop.sync.send",side_effect=RuntimeError("offline")):
            with self.assertRaises(RuntimeError):sync_once(Collector(),lambda:1800000000)
            self.assertEqual(changed,[])
        with patch("desktop.sync.read_settings",return_value=conf),patch(
            "desktop.sync.get_token",return_value="gep_android_test"),patch(
            "desktop.sync.git_observations",return_value=[]),patch(
            "desktop.sync.save_settings",side_effect=lambda x:changed.append(dict(x))),patch(
            "desktop.sync.send",return_value={"accepted":1,"duplicates":0}):
            result=sync_once(Collector(),lambda:1800000000)
        self.assertEqual(result["accepted"],1)
        self.assertGreater(changed[-1]["last_sync_ms"],0)
