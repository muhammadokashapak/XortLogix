# stt_engine.py
"""
High-Speed Speech-to-Text (STT) Engine with Universal Audio Stream Support.
Handles raw 16kHz PCM, WAV, and containerized audio streams.
Eliminates multi-dialect race conditions and provides ultra-fast transcription
with Sales Domain Context Biasing. Supports Groq Whisper Cloud (80ms) + Local Fallback.
"""

import os
import io
import time
import re
import json
import logging
import asyncio
from typing import Optional, Dict, Any

import requests
import speech_recognition as sr

logger = logging.getLogger("STTEngine")

SALES_INITIAL_PROMPT = (
    "Sales conversation: NDA, IP security, source code, pricing, discount, budget, "
    "timeline, deadline, milestone, fixed-price, hourly rate, React, Python, QA testing, "
    "software development, deliverables, Upwork, freelancer, contract, warranty."
)

class STTEngine:
    def __init__(self, model_name: str = "base", device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 120
        self.recognizer.dynamic_energy_threshold = False
        
        # Check Groq API Key for ultra-fast 80ms Whisper
        self.groq_api_key = os.environ.get("GROQ_API_KEY", "").strip()
        if self.groq_api_key:
            logger.info("⚡ Groq Whisper Cloud API Key detected! Ultra-fast <120ms STT active.")

    def _convert_bytes_to_audio_data(self, audio_bytes: bytes, suffix: str = ".wav") -> Optional[sr.AudioData]:
        """Converts raw audio bytes or WAV bytes into 16kHz PCM AudioData."""
        if not audio_bytes or len(audio_bytes) < 200:
            return None

        clean_suf = suffix.lower().replace(".", "")

        # 1. Direct raw 16kHz 16-bit PCM
        if clean_suf in ("raw_pcm", "rawpcm", "pcm"):
            if len(audio_bytes) % 2 != 0:
                audio_bytes = audio_bytes[:-1]
            if len(audio_bytes) < 1600:  # less than 0.05s
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

    def _transcribe_groq(self, audio_data: sr.AudioData) -> Optional[str]:
        """Transcribes using Groq Whisper Cloud in <120ms with sales prompt biasing."""
        if not self.groq_api_key:
            return None
        try:
            wav_bytes = audio_data.get_wav_data(convert_rate=16000, convert_width=2)
            headers = {"Authorization": f"Bearer {self.groq_api_key}"}
            files = {
                "file": ("audio.wav", wav_bytes, "audio/wav"),
                "model": (None, "whisper-large-v3-turbo"),
                "prompt": (None, SALES_INITIAL_PROMPT),
                "language": (None, "en"),
                "response_format": (None, "json")
            }
            res = requests.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers=headers,
                files=files,
                timeout=3.5
            )
            if res.status_code == 200:
                text = res.json().get("text", "").strip()
                if text:
                    return text
        except Exception as e:
            logger.debug(f"Groq STT note: {e}")
        return None

    def transcribe_audio_bytes(self, audio_bytes: bytes, suffix: str = ".wav") -> Dict[str, Any]:
        """
        Transcribes audio bytes accurately without dialect race conditions.
        Returns transcribed text, detected language, and latency.
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

        # 1. Try Groq Whisper Cloud if key configured (Ultra-fast <120ms)
        if self.groq_api_key:
            groq_text = self._transcribe_groq(audio_data)
            if groq_text:
                latency_ms = int((time.time() - start_time) * 1000)
                logger.info(f"⚡ Groq Whisper Transcribed ({latency_ms}ms): '{groq_text}'")
                return {
                    "success": True,
                    "text": groq_text,
                    "language": "en-US",
                    "engine": "groq-whisper",
                    "latency_ms": latency_ms
                }

        # 2. Local Google STT — Single-Model Primary (Eliminating Race Condition Bug)
        try:
            rec = sr.Recognizer()
            rec.energy_threshold = 120
            rec.dynamic_energy_threshold = False
            
            # Primary English (en-US)
            en_text = rec.recognize_google(audio_data, language="en-US")
            if en_text and len(en_text.strip()) > 1:
                latency_ms = int((time.time() - start_time) * 1000)
                logger.info(f"⚡ Speech Transcribed ({latency_ms}ms) [en-US]: '{en_text.strip()}'")
                return {
                    "success": True,
                    "text": en_text.strip(),
                    "language": "en-US",
                    "latency_ms": latency_ms
                }
        except Exception:
            pass

        # 3. Fallback: Secondary Indian English / Regional Dialect
        try:
            rec = sr.Recognizer()
            in_text = rec.recognize_google(audio_data, language="en-IN")
            if in_text and len(in_text.strip()) > 1:
                latency_ms = int((time.time() - start_time) * 1000)
                logger.info(f"⚡ Speech Transcribed ({latency_ms}ms) [en-IN]: '{in_text.strip()}'")
                return {
                    "success": True,
                    "text": in_text.strip(),
                    "language": "en-IN",
                    "latency_ms": latency_ms
                }
        except Exception:
            pass

        return {
            "success": False,
            "text": "",
            "error": "No speech detected in audio slice.",
            "latency_ms": int((time.time() - start_time) * 1000)
        }

    async def transcribe_async(self, audio_bytes: bytes, suffix: str = ".wav") -> Dict[str, Any]:
        return await asyncio.to_thread(self.transcribe_audio_bytes, audio_bytes, suffix)

