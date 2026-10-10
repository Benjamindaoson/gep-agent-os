# GEP Agent OS — Experimental Windows & Android Companions

This is the first downloadable **pre-release** of the optional device collectors. The primary GEP product remains web-first.

## Assets
- **GEP-Companion-Windows-x64.exe** — portable unsigned Windows companion built via PyInstaller. Uses the external ActivityWatch service for app-usage aggregates and optionally selected local Git repositories (metadata only).
- **GEP-Companion-Android-debug.apk** — experimental Android debug APK (not a Google Play production-signed release). Opt-in Android usage statistics require permission in Settings.
- **SHA256SUMS.txt** — hashes of both artifacts.

## Installation requirements
Both clients need a **deployed, HTTPS GEP Cloud backend** and an account for pairing. Windows also requires ActivityWatch to run separately for automatic observation. For Android, users must explicitly grant Usage Access. These executables do **not** install a public GEP server, OpenClaw, OpenHands, or ActivityWatch.

## Important limitations
- **Not production-ready.** No physical-device end-to-end acceptance, security penetration review, code signing, or public SaaS deployment has been completed.
- Cloud background Agent execution is limited to planning drafts in this build; arbitrary autonomous external work is not available.
- The Windows collector sends app names and aggregate durations, plus optional Git repository name/branch/short SHA/dirty flag. It does not capture keystrokes, screenshots, or window titles.
- Android app usage statistics can be incomplete because of OS background restrictions. This release does not claim complete device monitoring.
- No raw browser URLs, messages, contacts, screenshots, or full file contents are collected by these companions.

## Source and documentation
- [Repository](https://github.com/Benjamindaoson/gep-agent-os)
- [Windows setup](https://github.com/Benjamindaoson/gep-agent-os/blob/main/desktop/README.md)
- [Android setup](https://github.com/Benjamindaoson/gep-agent-os/blob/main/android/README.md)
- [Cloud deployment](https://github.com/Benjamindaoson/gep-agent-os/blob/main/cloud/DEPLOYMENT.md)

Please evaluate with non-sensitive test data and report failures through GitHub Issues.
