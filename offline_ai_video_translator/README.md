# Offline AI Video Translator Android App

An advanced, 100% offline, on-device AI-powered media player for Android built with **Kotlin**, **Jetpack Compose**, **Material 3**, **Android Media3 / ExoPlayer**, **Room Database**, and **ONNX Runtime Mobile**.

Select any video or audio file from your device, and the app will locally transcribe spoken speech, translate it into your target language (e.g. Urdu, Spanish, Arabic, French, German, Hindi, etc.), and render synchronized real-time dual subtitles — with **ZERO cloud dependencies, ZERO API keys, and 100% offline execution** (airplane mode compatible).

---

## 🌟 Key Features

* **100% Offline AI Execution**: Runs completely on-device without internet access, external servers, or paid APIs.
* **Universal Media Playback**: Powered by Android Media3 / ExoPlayer supporting MP4, MKV, WebM, MOV, MP3, WAV, AAC, M4A, and FLAC.
* **On-Device Speech Recognition (STT)**: Energy-based Voice Activity Detection (VAD) + 80-channel Mel Spectrogram extraction + quantized Whisper ONNX inference.
* **Offline Neural Machine Translation (NMT)**: Autoregressive Seq2Seq translation using MarianMT / OPUS-MT ONNX models with subword tokenization.
* **Real-Time Synchronized Subtitles**: Smooth, frame-accurate subtitle alignment with Media3 playback time, adjustable delays, font scaling, and high-contrast translucent backgrounds.
* **Dual Subtitle Modes**: View Original Only, Translation Only, or Original + Translation simultaneously.
* **Smart Persistence & Caching**: Room database caching prevents reprocessing previously analyzed media files.
* **Export Subtitles**: Export generated transcripts and translations to standard `.srt` (SubRip) or `.vtt` (WebVTT) files.
* **SAF Storage Integration**: Seamlessly pick files from device storage or external apps using Android's Storage Access Framework.
* **Model Manager**: In-app AI model status check, model import tools, and memory management.

---

## 🏗️ Architecture Overview

The app follows **Clean Architecture** with **MVVM (Model-View-ViewModel)** and **Unidirectional Data Flow (UDF)**:

```text
UI (Jetpack Compose + Material 3)
         │
    ViewModel (StateFlow & Coroutines)
         │
    Domain UseCases (ProcessMediaUseCase, GetSubtitlesUseCase, ManageModelsUseCase)
         │
    ┌────────────────────────┬─────────────────────────┬─────────────────────────┐
    │                        │                         │                         │
Media Engine            AI Pipeline Subsystem     Persistence Subsystem      Settings & DataStore
(Media3 / ExoPlayer)    ├── AudioExtractor (PCM)  ├── AppDatabase (Room)     └── PreferencesDataStore
                        ├── VadDetector           │   ├── MediaDao
                        ├── WhisperOnnxEngine     │   ├── TranslationJobDao
                        ├── MarianOnnxEngine      │   └── SubtitleDao
                        └── ModelManager          └── File Cache
```

For a deep dive into data structures, memory management, and pipeline stages, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## 📥 Model Installation

For detailed instructions on obtaining, converting, and installing the required ONNX models, refer to [MODEL_SETUP.md](MODEL_SETUP.md).

Quick summary:
1. Place `whisper_tiny_quant.onnx` in `/data/data/com.example.offlinetranslator/files/models/speech/`
2. Place `opus_mt_en_ur.onnx` in `/data/data/com.example.offlinetranslator/files/models/translation/en_ur/`
3. Or tap **"Import Model File"** in the app's **Settings & AI Models** screen to pick files directly from storage.

---

## 🛠️ Build & Run

Ensure you have Android Studio Hedgehog (or later) with JDK 17.

```bash
# Clone the repository
git clone https://github.com/example/offline-video-translator.git
cd offline-video-translator

# Build debug APK
./gradlew assembleDebug

# Run unit tests
./gradlew test
```

For complete step-by-step build guides, APK extraction paths, and Android installation, see [BUILD.md](BUILD.md).

---

## 🧪 Testing

Comprehensive unit tests are located in `app/src/test/java/com/example/offlinetranslator/`:
* `SubtitleSyncTest.kt`: Subtitle matching, binary search accuracy, and delay offsets.
* `TimeUtilsTest.kt`: Duration formatting, SRT timestamp generation, and SRT/VTT parsing.
* `TranslationEngineTest.kt`: Tokenizer encode/decode and Voice Activity Detection (VAD) audio partitioning.

Run tests via:
```bash
./gradlew testDebugUnitTest
```

---

## 📄 Documentation Sitemap

* [MODEL_SETUP.md](MODEL_SETUP.md) — Model downloads, formats, licenses, and memory requirements.
* [ARCHITECTURE.md](ARCHITECTURE.md) — Component architecture, state flows, and audio processing pipeline.
* [BUILD.md](BUILD.md) — Gradle build commands, APK generation, and device installation.
* [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — Common error resolution, RAM optimizations, and format compatibility.

---

## ⚖️ License & Privacy

* **100% Private**: No user media or audio is ever uploaded to any server. Everything remains strictly on your device.
* **License**: MIT License.
