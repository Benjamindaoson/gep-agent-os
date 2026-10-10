import unittest, tempfile
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
from desktop.collector import app_seconds,ActivityWatchCollector,git_status
class CollectorTests(unittest.TestCase):
    def test_event_clipping_without_window_titles(self):
        start=1_800_000_000_000
        dt=datetime.fromtimestamp((start-5000)/1000,timezone.utc).isoformat()
        samples=[{"timestamp":dt,"duration":20,"data":{"app":"Code","title":"private.txt"}}]
        totals=app_seconds(samples,start,start+10000)
        self.assertEqual(totals,{"Code":10})
        self.assertNotIn("private",str(totals))
    def test_multiple_bucket_source(self):
        start=1_800_000_000_000
        dt=datetime.fromtimestamp(start/1000,timezone.utc).isoformat()
        aw=ActivityWatchCollector()
        def get(path):
            if path.endswith("/buckets/"):return {"aw-watcher-window_x":{}}
            return [{"timestamp":dt,"duration":15,"data":{"app":"Code"}}]
        with patch.object(aw,"_get",side_effect=get):
            records=aw.collect(start,start+20000)
        self.assertEqual(records[0]["seconds"],15)
    def test_invalid_source(self):
        with self.assertRaises(ValueError):ActivityWatchCollector("https://somewhere.net")
