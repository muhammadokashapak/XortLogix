# stt_engine.py
"""
Speech-to-Text (STT) Engine with Universal Browser & Audio Stream Support.
Handles raw PCM, WAV, WebM, and MP3 streams.
Uses multi-dialect Google Speech Recognition (en-US, en-IN, ur-PK) for high-accuracy
transcription of client & sales rep voices from Google Meet, Zoom, and Mic.
"""

import os
import io
import time
import wave
import struct
import logging
import asyncio
from typing import Optional, Dict, Any

import speech_recognition as sr

logger = logging.getLogger("STTEngine")

class STTEngine:
    def __init__(self, model_name: str = "base", device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 200
        self.recognizer.dynamic_energy_threshold = True

    def _convert_bytes_to_audio_data(self, audio_bytes: bytes, suffix: str = ".wav") -> Optional[sr.AudioData]:
        """Converts raw audio bytes or WAV bytes into 16kHz PCM AudioData."""
        if not audio_bytes or len(audio_bytes) < 200:
            return None

        clean_suf = suffix.lower().replace(".", "")

        # 1. Direct raw 16kHz 16-bit PCM
        if clean_suf in ("raw_pcm", "rawpcm", "pcm"):
            if len(audio_bytes) % 2 != 0:
                audio_bytes = audio_bytes[:-1]
            if len(audio_bytes) < 1600: # less than 0.05s
                return None
            return sr.AudioData(audio_bytes, 16000, 2)

        # 2. Standard WAV Container
        try:
            with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
                return self.recognizer.record(source)
        except Exception:
            pass

        # 3. Try PyAV decoding for containerized WebM / MP3 / OGG
        try:
            import av
            container = av.open(io.BytesIO(audio_bytes))
            if container.streams.audio:
                resampler = av.AudioResampler(format='s16', layout='mono', rate=16000)
                pcm_chunks = []
                for frame in container.decode(audio=0):
                    for rf in resampler.resample(frame):
                        pcm_chunks.append(rf.to_ndarray().tobytes())
                if pcm_chunks:
                    raw_pcm = b"".join(pcm_chunks)
                    if len(raw_pcm) >= 1600:
                        return sr.AudioData(raw_pcm, 16000, 2)
        except Exception:
            pass

        # 4. Fallback: treat as raw PCM
        if len(audio_bytes) >= 1600:
            if len(audio_bytes) % 2 != 0:
                audio_bytes = audio_bytes[:-1]
            return sr.AudioData(audio_bytes, 16000, 2)

        return None

    def transcribe_audio_bytes(self, audio_bytes: bytes, suffix: str = ".wav") -> Dict[str, Any]:
        """
        Transcribes audio bytes using concurrent multi-dialect speech recognition.
        Returns transcribed text, detected dialect, and latency.
        """
        if not audio_bytes:
            return {"success": False, "text": "", "error": "Empty audio data", "latency_ms": 0}

        start_time = time.time()
        audio_data = self._convert_bytes_to_audio_data(audio_bytes, suffix=suffix)
        if audio_data is None:
            return {
                "success": False,
                "text": "",
                "error": "Audio chunk too short or silent.",
                "latency_ms": int((time.time() - start_time) * 1000)
            }

        # Multi-dialect parallel recognition: return the fastest response immediately
        languages = ["en-US", "ur-PK"]
        
        def _try_lang(lang: str):
            try:
                rec = sr.Recognizer()
                rec.energy_threshold = 150
                rec.dynamic_energy_threshold = False
                res_text = rec.recognize_google(audio_data, language=lang)
                if res_text and len(res_text.strip()) > 1:
                    return (lang, res_text.strip())
            except Exception:
                pass
            return (lang, None)

        from concurrent.futures import ThreadPoolExecutor, as_completed
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(_try_lang, lang) for lang in languages]
            for future in as_completed(futures):
                lang, text = future.result()
                if text:
                    latency_ms = int((time.time() - start_time) * 1000)
                    logger.info(f"⚡ Speech Transcribed ({latency_ms}ms) [{lang}]: '{text}'")
                    return {
                        "success": True,
                        "text": text,
                        "language": lang,
                        "latency_ms": latency_ms
                    }

        return {
            "success": False,
            "text": "",
            "error": "No speech detected in audio slice.",
            "latency_ms": int((time.time() - start_time) * 1000)
        }

    async def transcribe_async(self, audio_bytes: bytes, suffix: str = ".wav") -> Dict[str, Any]:
        return await asyncio.to_thread(self.transcribe_audio_bytes, audio_bytes, suffix)
