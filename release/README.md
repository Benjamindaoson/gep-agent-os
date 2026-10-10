# GitHub Releases

This repository publishes tagged **prereleases** under the GitHub **Releases**
tab, with Android APK and Windows EXE attached as assets. The source of truth
is `release/VERSION`; the workflow builds from the exact `main` commit that
changes it and only publishes if core, cloud, Windows and Android jobs succeed.

Release automation:
- `.github/workflows/release.yml`
- `release/VERSION`
- `release/RELEASE_NOTES.md`

Publishing via CI uses the repository's GitHub Actions token with
`contents: write`. It does not need external access tokens.
The release job fails closed if a tag already exists or an artifact is missing.

IMPORTANT: Do not advertise this alpha as production-ready, as having complete
cross-device orchestration, or as being a mobile-store-signed app. It is for
early device integration tests only.

To create a future prerelease: update `release/VERSION`, amend release notes,
and push the change to `main`. Verify CI and the release details afterwards.
