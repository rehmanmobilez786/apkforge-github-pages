# Android Source Starter

A reusable Android app foundation built with Expo, React Native, TypeScript, and Expo Router.

It includes:

- A GitHub Pages APK Builder website with source-upload and build buttons
- A polished three-tab mobile shell
- Home dashboard with starter modules
- Toolbox screen with reusable app patterns
- Detail screens with persistent bookmarks
- AsyncStorage-backed local preferences
- Light and dark semantic color tokens
- Android package configuration
- GitHub Actions workflow that builds a release APK

## Run locally

```bash
pnpm install
pnpm --filter @workspace/android-source-starter run dev
```

Use the mobile preview or scan the QR code with Expo Go. The preview server supplies the correct Replit environment values automatically.

## Build the APK locally

The GitHub workflow uses the same native Android build path:

```bash
pnpm install
pnpm exec expo prebuild --non-interactive --platform android
cd android
./gradlew assembleRelease
```

The APK is generated at:

```text
android/app/build/outputs/apk/release/app-release.apk
```

## GitHub APK builds

Push the repository to GitHub and open the **Actions** tab. The `Build Android APK` workflow runs on pushes to `main` and can also be started manually. The generated APK is uploaded as a workflow artifact.

## Simple website flow

This repository includes a GitHub Pages website in `docs/index.html`.

1. Create a GitHub repository and upload everything inside the `artifacts/android-source-starter` folder to the repository root, including the `.github` folder.
2. In GitHub, open **Settings → Pages** and choose **GitHub Actions** as the source.
3. Open the deployed Pages website and paste the repository URL.
4. Click **Upload source code**. GitHub opens its source upload page.
5. Upload or replace your Android source files at the repository root. Keep `.github/workflows/android-apk.yml`.
6. The upload starts the APK workflow automatically.
7. Click **Open APK build**, open the completed workflow, and download the APK from **Artifacts**.

The website only redirects to GitHub's own upload and Actions pages. No source code is sent to a third-party server and no GitHub token is stored in the website.

## Customize it

1. Update the app identity in `app.json`.
2. Replace the icon at `assets/images/icon.png`.
3. Edit semantic colors in `constants/colors.ts`.
4. Add screens under `app/`.
5. Add shared state in `context/`.
6. Update the workflow if your app needs extra native Android setup.

## Project layout

```text
app/                 Expo Router screens
components/          Shared scaffold components
constants/           Theme tokens
context/             Persistent app state
hooks/               Reusable hooks
assets/images/       App icon and image assets
.github/workflows/   Automated APK build
```