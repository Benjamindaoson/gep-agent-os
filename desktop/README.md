# GEP Windows Companion

**Optional** Windows activity collector and Git metadata sync for the GEP hosted service.

GEP itself remains usable from any browser, with no client required.
This companion enhances observation on **Windows**; it is not a replacement for
OpenClaw/OpenHands or a full remote-desktop agent.

## Built on existing open source

- [ActivityWatch](https://github.com/ActivityWatch/activitywatch): use its real
  window watcher/server rather than copying/reimplementing monitoring code.
- GEP includes a small adapter that reads ActivityWatch **locally**, reporting
  only app name and clipped duration.
- [OpenClaw](https://github.com/openclaw/openclaw) remains a separate optional
  execution node. Activity observation does not grant remote shell permissions.
- Keyring integrates with Windows Credential Manager; pystray provides a tray UI.

ActivityWatch is MPL-2.0. We are using a **separately installed service via
HTTP API**, not incorporating its files into a distributed Windows executable.

## Test / build

```powershell
python -m pip install -r desktop/requirements.txt
python -m unittest discover -s desktop/tests -v
python -m PyInstaller --onefile --windowed --name GEP-Companion --collect-all keyring desktop/launcher.py
```

The Windows GitHub Actions job compiles `dist/GEP-Companion.exe` and attaches
the unsigned test build as an artifact. Building does not prove real user device
or hosted-account end-to-end functionality.

## Pair and use

1. Deploy your GEP cloud API on an HTTPS URL.
2. From the GEP web dashboard, create a Windows device token. Copy it once.
3. Install and launch ActivityWatch separately on Windows. Verify its local
   dashboard on `http://127.0.0.1:5600`.
4. Launch GEP-Companion.exe, enter the HTTPS GEP URL and token, and select Pair.
5. Optionally add Git repository folders (only selected repo name, branch,
   short commit SHA and dirty state are collected).
6. Click Start / resume; click Sync now for a first upload.
7. View the same computer activity from a signed-in phone or desktop browser.
8. Pause from the companion, or revoke the token/delete observations through the web UI.

The companion is not scheduled to autostart with Windows by default; running
in the system tray allows background sync while the app remains open.
No automatic screenshots, browsing history, source code contents or credentials
are uploaded.

## Verification gates

- Windows EXE builds on GitHub Actions.
- Authenticated pairing and token revocation work against a real HTTPS backend.
- The actual ActivityWatch window watcher generates events during a consented session.
- Cloud API accepts the batch; duplicates do not inflate app duration.
- Second browser session on Android reads the same data.
- Pause stops uploading; device revocation prevents future uploads.
- Git observation never contains filenames, diffs, full commit history or source.

These **live gates are pending** until an authorized Windows host and deployed
GEP backend are available.
