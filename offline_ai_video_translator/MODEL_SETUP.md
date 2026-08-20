# AI Model Setup Guide (Offline Video Translator)

This document provides complete, step-by-step instructions on obtaining, preparing, and installing the on-device AI models for speech recognition (STT) and neural machine translation (NMT).

---

## 1. Speech Recognition Model (STT)

### Model Details
* **Architecture**: OpenAI Whisper (Tiny / Base) exported to ONNX format with INT8 quantization.
* **Input**: 80-channel Log Mel-Spectrogram (16kHz mono audio).
* **Output**: Token sequences representing transcribed speech.
* **Size**: 
  * Whisper-Tiny Quantized: **~39 MB**
  * Whisper-Base Quantized: **~75 MB**
* **RAM Requirement**: ~120 MB during inference.
* **License**: MIT License (OpenAI / ONNX Community).

### Obtaining the Model
Download pre-quantized ONNX models legally from Hugging Face or the official ONNX Runtime Model Zoo:

1. **Hugging Face Model Repositories**:
   * Repository: `onnx-community/whisper-tiny-ONNX` or `microsoft/whisper-tiny-onnx`
   * Target File: `whisper_tiny_quant.onnx` or `model.onnx`
2. **Alternative (Custom Export)**:
   You can export any Whisper model using Optimum:
   ```bash
   pip install optimum[onnxruntime] transformers
   optimum-cli export onnx --model openai/whisper-tiny --task automatic-speech-recognition ./whisper_onnx/
   ```

---

## 2. Machine Translation Model (NMT)

### Model Details
* **Architecture**: MarianMT / OPUS-MT (Seq2Seq Transformer).
* **Input**: Source sentence tokens (BPE subwords).
* **Output**: Translated target sentence tokens.
* **Size**: **~45 MB - 60 MB** per language pack (INT8 quantized).
* **RAM Requirement**: ~90 MB during inference.
* **License**: CC-BY-4.0 / Apache 2.0 (Helsinki-NLP).

### Available Language Pairs & Sources
Helsinki-NLP provides over 1,000 language pair models on Hugging Face:

| Language Pair | Hugging Face Model Name | Output ONNX File Name |
| :--- | :--- | :--- |
| **English → Urdu** | `Helsinki-NLP/opus-mt-en-ur` | `opus_mt_en_ur.onnx` |
| **English → Spanish** | `Helsinki-NLP/opus-mt-en-es` | `opus_mt_en_es.onnx` |
| **English → Arabic** | `Helsinki-NLP/opus-mt-en-ar` | `opus_mt_en_ar.onnx` |
| **English → French** | `Helsinki-NLP/opus-mt-en-fr` | `opus_mt_en_fr.onnx` |
| **English → German** | `Helsinki-NLP/opus-mt-en-de` | `opus_mt_en_de.onnx` |
| **English → Hindi** | `Helsinki-NLP/opus-mt-en-hi` | `opus_mt_en_hi.onnx` |
| **English → Russian** | `Helsinki-NLP/opus-mt-en-ru` | `opus_mt_en_ru.onnx` |
| **English → Chinese** | `Helsinki-NLP/opus-mt-en-zh` | `opus_mt_en_zh.onnx` |

---

## 3. Storage Directory Hierarchy

Models are placed in the application's private internal storage directory:

```text
/data/data/com.example.offlinetranslator/files/
└── models/
    ├── speech/
    │   └── whisper_tiny_quant.onnx
    │
    └── translation/
        ├── en_ur/
        │   ├── model.onnx (or opus_mt_en_ur.onnx)
        │   └── vocab.json (or source.spm)
        ├── en_es/
        │   └── model.onnx
        ├── en_ar/
        │   └── model.onnx
        └── en_fr/
            └── model.onnx
```

---

## 4. Installation Methods

### Method A: In-App Import (Recommended for Users)
1. Launch the app on your Android device.
2. Tap the ⚙ **Settings** icon on the top right.
3. Scroll down to **Offline AI Models**.
4. Tap **"Import STT Model"** or **"Import MT Model"**.
5. Select your downloaded `.onnx` file using Android's file picker.
6. The app will automatically copy and register the model into internal storage.

### Method B: ADB Push (Recommended for Developers)
Connect your Android phone or emulator with USB debugging enabled:

```bash
# Push speech model
adb push whisper_tiny_quant.onnx /data/local/tmp/
adb shell "run-as com.example.offlinetranslator mkdir -p /data/data/com.example.offlinetranslator/files/models/speech"
adb shell "run-as com.example.offlinetranslator cp /data/local/tmp/whisper_tiny_quant.onnx /data/data/com.example.offlinetranslator/files/models/speech/"

# Push translation model (e.g. English to Urdu)
adb push opus_mt_en_ur.onnx /data/local/tmp/
adb shell "run-as com.example.offlinetranslator mkdir -p /data/data/com.example.offlinetranslator/files/models/translation/en_ur"
adb shell "run-as com.example.offlinetranslator cp /data/local/tmp/opus_mt_en_ur.onnx /data/data/com.example.offlinetranslator/files/models/translation/en_ur/model.onnx"
```

---

## 5. Adding New Language Pairs

To support additional translation languages:
1. Obtain the Helsinki-NLP MarianMT model for your desired pair (e.g., `opus-mt-en-it` for English to Italian).
2. Export or download the `.onnx` file.
3. Create a folder named `{source_code}_{target_code}` (e.g., `en_it`) in `models/translation/`.
4. Place `model.onnx` inside that folder.
5. In the app settings, tap **Refresh** and the new language pair will immediately appear with status **Installed**.

---

## 6. Hardware & Architecture Specifications

* **Supported ABIs**: `arm64-v8a` (recommended), `armeabi-v7a`, `x86_64`, `x86`.
* **Minimum Android Version**: Android 7.0 (API level 24).
* **Minimum RAM**: 2 GB RAM (3 GB+ recommended).
* **Storage Space**: ~150 MB for app + core models.
