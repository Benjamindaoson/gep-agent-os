import unittest
from unittest.mock import patch
from gep.cloud import CloudCLI,CloudActionError
class CloudTests(unittest.TestCase):
 def test_actions_are_never_implicit(self):
  cloud=CloudCLI()
  with self.assertRaises(ValueError):cloud.vercel_preview(".")
  with self.assertRaises(ValueError):cloud.runpod_stop("p123",approved=True)
  with self.assertRaises(ValueError):cloud.runpod_start("p123")
  with self.assertRaises(ValueError):cloud.runpod_stop("../bad",approved=True,data_safe=True)
 def test_vercel_runs_exact_cli_and_needs_external_verification(self):
  with patch("gep.cloud.shutil.which",return_value="/usr/bin/vercel"),patch(
    "gep.cloud._exec",return_value="https://preview.vercel.app") as exec_call:
   res=CloudCLI().vercel_preview(".",approved=True)
  self.assertEqual(res["status"],"submitted")
  self.assertIn("HTTP health",res["verification"])
  self.assertEqual(exec_call.call_args.args[0],["vercel","deploy","--yes"])
 def test_runpod_start_is_explicit(self):
  with patch("gep.cloud.shutil.which",return_value="/bin/runpodctl"),patch(
      "gep.cloud._exec",return_value="started") as cmd:
   result=CloudCLI().runpod_start("pod123",approved=True)
  self.assertEqual(result["operation"],"start")
  self.assertEqual(cmd.call_args.args[0],["runpodctl","pod","start","pod123"])
