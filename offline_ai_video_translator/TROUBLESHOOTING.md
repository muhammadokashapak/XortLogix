# Troubleshooting Guide (Offline Video Translator)

This guide covers solutions to common setup, runtime, model loading, and media playback issues.

---

## 1. AI Model Issues

### Symptom: "Offline model unavailable" or "Required model not installed"
* **Cause**: The application cannot find the `.onnx` model binary in `/files/models/speech/` or `/files/models/translation/`.
* **Fix**:
  1. Open **Settings** (gear icon in the top right of the app).
  2. Tap **"Import STT Model"** and select `whisper_tiny_quant.onnx`.
  3. Tap **"Import MT Model"** and select `opus_mt_en_ur.onnx` (or corresponding language pack).
  4. Tap the **Refresh** button on top of the Settings screen. The status will change to **Installed**.
  5. Consult [MODEL_SETUP.md](MODEL_SETUP.md) for download links.

---

## 2. Media Playback & Extraction Issues

### Symptom: "No audio track found in the selected media file"
* **Cause**: The video file has no audio stream, or uses a proprietary/unsupported audio codec.
* **Fix**:
  * Ensure the video actually has sound by playing it in a standard player.
  * Supported audio codecs: AAC, Opus, MP3, Vorbis, PCM, FLAC.

### Symptom: Subtitles are slightly out of sync with speech
* **Cause**: Variable frame rate (VFR) encoding or audio clock drift.
* **Fix**:
  1. While the media is playing, open the **Translation Settings** bottom sheet.
  2. Adjust the **Subtitle Delay (ms)** slider (e.g. `+200ms` or `-200ms`) to align the subtitles with the speaker's voice.

---

## 3. Low-End Device & Out-of-Memory (OOM) Issues

### Symptom: App slows down or gets killed during long videos (1+ hour)
* **Cause**: Low-end phones with 2 GB RAM or heavy background apps.
* **Optimization applied in app**:
  * The app processes audio in 15-25s chunks via Voice Activity Detection (VAD) rather than decoding the entire movie at once.
  * Models are unloaded when playback starts.
* **Recommended steps**:
  1. Use quantized INT8 models (`whisper_tiny_quant.onnx`) instead of FP32 or Base/Small models.
  2. Close background apps before starting translation of very long video files.

---

## 4. Storage & File Access Permissions

### Symptom: Media Picker fails to open files on Android 13+
* **Cause**: Android 13 (API 33) introduced granular media permissions (`READ_MEDIA_VIDEO` and `READ_MEDIA_AUDIO`).
* **Fix**:
  * The app automatically requests `READ_MEDIA_VIDEO` and `READ_MEDIA_AUDIO` on startup. If denied, go to Android **Settings → Apps → Offline AI Translator → Permissions** and grant access to **Photos & Videos** and **Music & Audio**.
