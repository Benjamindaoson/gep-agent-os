import unittest
from unittest.mock import patch
from datetime import datetime, timezone

from gep.activitywatch import ActivityWatchReader


class ActivityWatchTests(unittest.TestCase):
    def test_rejects_remote_hosts(self):
        with self.assertRaises(ValueError):
            ActivityWatchReader("https://example.com")

    def test_summarizes_only_app_without_titles(self):
        stamp = datetime.now(timezone.utc).isoformat()
        reader = ActivityWatchReader()
        def fake_get(path):
            if path.endswith("/buckets/"):
                return {"aw-watcher-window_demo": {}, "aw-watcher-afk_demo": {}}
            return [{"timestamp": stamp, "duration": 90, "data": {"app": "Code", "title": "secret document"}}]
        with patch.object(reader, "_get", side_effect=fake_get):
            result = reader.summary()
        self.assertEqual(result["app_seconds"], {"Code": 90.0})
        self.assertNotIn("secret document", str(result))


if __name__ == "__main__":
    unittest.main()
