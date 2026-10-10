# GEP Android Companion (experimental)

Android is the first mobile **activity-observation** test platform.
The zero-install, browser-based GEP assistant remains the default entrypoint.

## Features implemented

- Android UsageStatsManager event-based foreground app-duration aggregates.
- Explicit, user-granted Usage Access through system Settings.
- Manual sync or periodic WorkManager sync (~15 minutes, not exact).
- Per-device bearer token stored with Android Keystore AES-GCM.
- HTTPS upload to account-scoped GEP Cloud API.
- Device token revocation and activity deletion in cloud API.
- No Accessibility Service, screenshot collection, keylogging, location, SMS or contact access.

## Build in Android Studio

Open the `android/` folder with Android Studio (JDK 17, Android SDK 35).
Sync Gradle; build `app` and install the debug build to a personal test device.
You must explicitly grant Usage Access via the device Settings screen.

## Pairing (API)

1. Log in to GEP web app.
2. POST `/api/mobile/devices` with JSON `{"label":"My Android"}` in an authenticated browser session; copy the **one-time** token.
3. Enter the HTTPS base URL and token in Android Companion.
4. Grant Usage Access and run "Sync now".
5. GET `/api/mobile/usage` while logged in to inspect per-app totals.
6. DELETE `/api/mobile/devices/{id}` to revoke a device, or DELETE `/api/mobile/usage` to erase imported usage records.

Do not upload APKs containing fixed tokens or credentials. Never post device tokens in public repositories.

## Accuracy and OS limitations

UsageEvents may miss a session that began before a requested window, and vendors
can suppress or delay WorkManager. This is **partial observable app time**, not
complete screen time or a measure of meaningful progress. Background collection
requires a separate app and permission. Browsers alone cannot read phone-wide use.
App names are sent by package ID, not screen or browsing content.

This folder includes Gradle scripts but no binary wrapper JAR. Open Android
Studio and use its Gradle integration (or install Gradle locally). We have not
run a physical Android device test in CI.
