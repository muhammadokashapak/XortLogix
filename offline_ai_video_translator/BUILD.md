# Build & Installation Guide (Offline Video Translator)

This document explains how to build the APK, run unit tests, and install the application onto an Android device or emulator.

---

## 1. Prerequisites

* **Operating System**: Windows, macOS, or Linux
* **Java Development Kit (JDK)**: JDK 17 (recommended: Amazon Corretto 17, Eclipse Temurin 17, or Android Studio bundled JDK)
* **Android Studio**: Android Studio Hedgehog (2023.1.1) or newer
* **Android SDK**:
  * Compile SDK: `34` (Android 14)
  * Min SDK: `24` (Android 7.0)
  * Target SDK: `34`
  * NDK: Standard NDK bundle for `arm64-v8a`, `armeabi-v7a`, `x86_64`, `x86`

---

## 2. Building from Command Line

### Windows (PowerShell / Command Prompt)

```powershell
# Navigate to project directory
cd "e:\Okashaaaaa\Projects\Video Player"

# Clean build
.\gradlew.bat clean

# Run Unit Tests
.\gradlew.bat testDebugUnitTest

# Assemble Debug APK
.\gradlew.bat assembleDebug

# Assemble Release APK
.\gradlew.bat assembleRelease
```

### macOS / Linux (Bash / Zsh)

```bash
# Navigate to project directory
cd /path/to/Video\ Player

# Grant execute permission
chmod +x gradlew

# Run Unit Tests
./gradlew testDebugUnitTest

# Assemble Debug APK
./gradlew assembleDebug
```

---

## 3. Output APK Locations

Upon successful compilation:

* **Debug APK**:
  ```text
  app/build/outputs/apk/debug/app-debug.apk
  ```
* **Release APK** (unsigned):
  ```text
  app/build/outputs/apk/release/app-release-unsigned.apk
  ```

---

## 4. Installing on Android Device

### Method A: Via ADB (USB / Wi-Fi Debugging)

Ensure your phone has **Developer Options** and **USB Debugging** enabled:

```bash
# Verify device is connected
adb devices

# Install APK directly
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

### Method B: Direct File Transfer

1. Copy `app-debug.apk` to your phone's **Downloads** folder (via USB cable or Google Drive).
2. On your phone, open **Files** or **File Manager**.
3. Tap `app-debug.apk`.
4. If prompted, enable **"Install unknown apps"** for your file manager.
5. Tap **Install**.

---

## 5. Opening the Project in Android Studio

1. Launch **Android Studio**.
2. Select **File → Open...**
3. Select the `Video Player` root folder.
4. Wait for Gradle Sync to complete.
5. Select a connected device or emulator in the toolbar.
6. Click the green ▶ **Run** button (or press `Shift + F10`).
