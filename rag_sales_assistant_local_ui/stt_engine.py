# stt_engine.py
"""
Speech-to-Text (STT) Engine using Groq Cloud Whisper-large-v3 (Ultra Fast ~200-400ms)
with automatic fallback to local OpenAI Whisper.
"""

import os
import io
import time
import tempfile
import logging
import asyncio
from typing import Optional, Dict, Any

logger = logging.getLogger("STTEngine")

def _load_env_key():
    """Reads GROQ_API_KEY from environment or .env file."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key and os.path.exists(".env"):
        try:
            with open(".env", "r", encoding="utf-8-sig") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GROQ_API_KEY="):
                        api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
        except Exception:
            pass
    return api_key

class STTEngine:
    def __init__(self, model_name: str = "whisper-large-v3", device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self.local_model = None
        self.groq_client = None
        self._init_groq()
        self._ensure_ffmpeg()

    def _init_groq(self):
        """Initializes Groq client and pre-warms connection for sub-200ms speed."""
        api_key = _load_env_key()
        if api_key:
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=api_key)
                logger.info("⚡ Groq Whisper client initialized! Using whisper-large-v3-turbo.")
                # Pre-warm connection in a quick background thread
                import threading
                def _warm():
                    try:
                        import io, wave, struct
                        buf = io.BytesIO()
                        w = wave.open(buf, 'wb')
                        w.setnchannels(1)
                        w.setsampwidth(2)
                        w.setframerate(16000)
                        w.writeframes(struct.pack('<' + 'h'*1600, *[0]*1600))
                        w.close()
                        self.groq_client.audio.transcriptions.create(
                            file=('warm.wav', buf.getvalue()),
                            model='whisper-large-v3-turbo',
                            response_format='json'
                        )
                        logger.info("⚡ Groq connection pre-warmed! Ready for instant <200ms transcription.")
                    except Exception:
                        pass
                threading.Thread(target=_warm, daemon=True).start()
            except Exception as e:
                logger.warning(f"Could not initialize Groq client: {e}")
                self.groq_client = None
        else:
            logger.info("No GROQ_API_KEY found. Operating in local Whisper mode.")

    def _ensure_ffmpeg(self):
        """Ensures ffmpeg.exe is accessible in PATH."""
        try:
            import imageio_ffmpeg
            import shutil
            src = imageio_ffmpeg.get_ffmpeg_exe()
            dst_dir = os.path.dirname(src)
            dst = os.path.join(dst_dir, "ffmpeg.exe")
            if not os.path.exists(dst):
                shutil.copy(src, dst)
            if dst_dir not in os.environ.get("PATH", ""):
                os.environ["PATH"] = dst_dir + os.pathsep + os.environ["PATH"]
        except Exception as e:
            logger.warning(f"Could not auto-configure ffmpeg: {e}")

    def load_local_model(self):
        """Loads local Whisper model on demand if Groq is not used."""
        if self.local_model is not None:
            return self.local_model
            
        try:
            logger.info(f"Loading local Whisper model: 'base' on {self.device}...")
            import whisper
            start = time.time()
            self.local_model = whisper.load_model("base", device=self.device)
            logger.info(f"Local Whisper loaded in {time.time() - start:.2f}s")
            return self.local_model
        except Exception as e:
            logger.error(f"Failed to load local Whisper model: {e}")
            return None

    def transcribe_audio_bytes(self, audio_bytes: bytes, suffix: str = ".wav") -> Dict[str, Any]:
        """
        Transcribes raw audio bytes using Groq Whisper-large-v3-turbo (~150-250ms).
        """
        if not audio_bytes or len(audio_bytes) < 400:
            return {"success": False, "text": "", "error": "Empty audio data", "latency_ms": 0}

        start_time = time.time()
        
        # 1. Try Groq Cloud Whisper Turbo first (~150ms - 250ms)
        if self.groq_client is not None:
            try:
                filename = f"audio{suffix}"
                transcription = self.groq_client.audio.transcriptions.create(
                    file=(filename, audio_bytes),
                    model="whisper-large-v3-turbo",
                    response_format="json",
                    temperature=0.0
                )
                text = transcription.text.strip()
                # Filter Whisper hallucinations on silence / quiet audio
                lower = text.lower().strip(".,!?:; ")
                if lower in ["you", "thank you", "thanks for watching", "subtitles by", "bye", "okay", "um", "ah", ""]:
                    text = ""

                latency_ms = int((time.time() - start_time) * 1000)
                if text:
                    logger.info(f"⚡ [Groq Whisper Turbo] ({latency_ms}ms): {text}")
                return {
                    "success": bool(text),
                    "text": text,
                    "language": "auto",
                    "latency_ms": latency_ms,
                    "provider": "groq"
                }
            except Exception as e:
                logger.warning(f"Groq Whisper Turbo failed, trying standard: {e}")
                try:
                    transcription = self.groq_client.audio.transcriptions.create(
                        file=(f"audio{suffix}", audio_bytes),
                        model="whisper-large-v3",
                        response_format="json",
                        temperature=0.0
                    )
                    text = transcription.text.strip()
                    latency_ms = int((time.time() - start_time) * 1000)
                    return {
                        "success": True,
                        "text": text,
                        "language": "auto",
                        "latency_ms": latency_ms,
                        "provider": "groq"
                    }
                except Exception as ex2:
                    logger.warning(f"Groq Whisper fallback failed: {ex2}")

        # 2. Local Whisper Fallback
        if self.local_model is None:
            self.load_local_model()

        if self.local_model is None:
            return {
                "success": False,
                "text": "",
                "error": "Both Groq and Local Whisper failed to initialize",
                "latency_ms": int((time.time() - start_time) * 1000)
            }

        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(audio_bytes)
                temp_path = tmp.name

            result = self.local_model.transcribe(
                temp_path,
                fp16=False,
                language=None,
                task="transcribe"
            )

            text = result.get("text", "").strip()
            detected_lang = result.get("language", "auto")
            latency_ms = int((time.time() - start_time) * 1000)

            logger.info(f"[Local Whisper] ({latency_ms}ms) [{detected_lang}]: {text}")
            return {
                "success": True,
                "text": text,
                "language": detected_lang,
                "latency_ms": latency_ms,
                "provider": "local"
            }
        except Exception as e:
            logger.error(f"Whisper transcription error: {e}")
            return {
                "success": False,
                "text": "",
                "error": str(e),
                "latency_ms": int((time.time() - start_time) * 1000)
            }
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    async def transcribe_async(self, audio_bytes: bytes, suffix: str = ".wav") -> Dict[str, Any]:
        """Asynchronously executes transcription in a thread pool to avoid blocking the event loop."""
        return await asyncio.to_thread(self.transcribe_audio_bytes, audio_bytes, suffix)
