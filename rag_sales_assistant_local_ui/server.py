# server.py
"""
FastAPI Server & WebSocket Gateway for Local AI Sales Assistant.
Provides real-time STT, RAG retrieval, Ollama LLM response streaming,
and serves the modern HTML5/CSS3/JavaScript Glassmorphism UI.
"""

import os
import re
import time
import json
import base64
import logging
import asyncio
from typing import Dict, Any, List, Optional

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from rag_engine import RAGEngine
from stt_engine import STTEngine

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SalesAssistantServer")

# Initialize FastAPI app
app = FastAPI(
    title="Local AI Sales Assistant (Voice RAG Co-Pilot)",
    description="Real-Time Local AI Sales Assistant with Whisper STT, ChromaDB RAG, and Ollama LLM",
    version="2.0.0"
)

# CORS middleware for open local access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Initialize engines
rag_engine = RAGEngine(
    pdf_path=os.path.join(BASE_DIR, "zoom.pdf"),
    chroma_path=os.path.join(BASE_DIR, "chroma_db_v2"),
    min_relevance=0.35,
    ollama_base_url="http://127.0.0.1:11434",
    llm_model="llama3.2:3b"
)

stt_engine = STTEngine(model_name="base", device="cpu")

# Connected WebSocket clients
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Client disconnected. Total active: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

# --- Autonomous Desktop Audio Listener (Decoupled Producer-Consumer WASAPI Loopback) ---
import threading
import queue
import warnings

class DesktopAudioListener:
    def __init__(self, stt, rag, broadcast_fn):
        self.stt = stt
        self.rag = rag
        self.broadcast_fn = broadcast_fn
        self.is_running = False
        self.capture_thread: Optional[threading.Thread] = None
        self.worker_thread: Optional[threading.Thread] = None
        self.audio_queue: queue.Queue = queue.Queue(maxsize=50)
        self.device_name = "Not Initialized"
        self.sentence_buffer: List[str] = []
        self.last_chunk_time: float = 0.0
        self.last_analyzed_sentence: str = ""
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.chunk_counter = 0

    def start(self, loop: asyncio.AbstractEventLoop):
        if self.is_running:
            return
        self.loop = loop
        self.is_running = True
        
        # 1. Start dedicated Whisper Consumer Worker Thread
        self.worker_thread = threading.Thread(target=self._process_queue_worker, daemon=True, name="WhisperWorkerConsumer")
        self.worker_thread.start()
        
        # 2. Start dedicated WASAPI Audio Capture Producer Thread
        self.capture_thread = threading.Thread(target=self._run_capture_loop, daemon=True, name="WASAPICaptureProducer")
        self.capture_thread.start()
        
        logger.info("🎙️ Autonomous Desktop Audio Listener (WASAPI Producer-Consumer) started.")

    def stop(self):
        self.is_running = False
        logger.info("🛑 Autonomous Desktop Audio Listener stopped.")

    def _run_capture_loop(self):
        """Dedicated audio capture loop: reads 16kHz frames continuously with zero blocking."""
        warnings.filterwarnings("ignore")
        try:
            import soundcard as sc
            import numpy as np
        except ImportError:
            logger.warning("soundcard or numpy not available for WASAPI capture.")
            self.is_running = False
            return

        SAMPLE_RATE = 16000
        FRAME_SIZE = 2048  # 128ms per frame
        SILENCE_TRIGGER_FRAMES = 4  # ~500ms natural clause pause
        MIN_SPEECH_FRAMES = 3      # ~380ms min speech
        MAX_SPEECH_FRAMES = 25     # ~3.2s max speech buffer per chunk

        while self.is_running:
            try:
                spk = sc.default_speaker()
                if not spk:
                    time.sleep(1.0)
                    continue

                loopback_mic = sc.get_microphone(id=str(spk.name), include_loopback=True)
                self.device_name = loopback_mic.name
                logger.info(f"⚡ [WASAPI LOOPBACK CAPTURE] Active on: {self.device_name}")

                pcm_buffer: List[bytes] = []
                speech_active = False
                silence_counter = 0

                with loopback_mic.recorder(samplerate=SAMPLE_RATE, channels=1, blocksize=FRAME_SIZE) as mic:
                    while self.is_running:
                        try:
                            data = mic.record(numframes=FRAME_SIZE)
                        except Exception:
                            time.sleep(0.02)
                            continue

                        if data is None or len(data) == 0:
                            continue

                        # Calculate RMS energy
                        rms = float(np.sqrt(np.mean(data ** 2)))
                        is_speech = rms >= 0.0035

                        int16_bytes = np.clip(data * 32767, -32768, 32767).astype(np.int16).tobytes()

                        if is_speech:
                            speech_active = True
                            silence_counter = 0
                            pcm_buffer.append(int16_bytes)
                        else:
                            if speech_active:
                                pcm_buffer.append(int16_bytes)
                                silence_counter += 1

                        # Natural pause (500ms) or max phrase buffer (3.2s) reached
                        natural_pause = speech_active and (silence_counter >= SILENCE_TRIGGER_FRAMES) and (len(pcm_buffer) >= MIN_SPEECH_FRAMES)
                        max_reached = len(pcm_buffer) >= MAX_SPEECH_FRAMES

                        if (natural_pause or max_reached) and len(pcm_buffer) >= MIN_SPEECH_FRAMES:
                            full_pcm_bytes = b"".join(pcm_buffer)
                            self.chunk_counter += 1
                            
                            # Clean VAD buffer state immediately!
                            pcm_buffer = []
                            speech_active = False
                            silence_counter = 0

                            logger.info(f"🎤 [WASAPI VAD] Audio chunk #{self.chunk_counter} detected ({len(full_pcm_bytes)} bytes) → Enqueueing for Whisper")

                            # Put into queue without blocking the WASAPI recorder loop!
                            try:
                                self.audio_queue.put_nowait((self.chunk_counter, full_pcm_bytes))
                            except queue.Full:
                                try:
                                    self.audio_queue.get_nowait()
                                except queue.Empty:
                                    pass
                                self.audio_queue.put_nowait((self.chunk_counter, full_pcm_bytes))

            except Exception as e:
                logger.warning(f"WASAPI capture loop note: {e}")
                time.sleep(0.5)

    def _process_queue_worker(self):
        """Dedicated consumer worker thread: processes audio chunks with Whisper & RAG."""
        while self.is_running:
            try:
                try:
                    chunk_id, pcm_bytes = self.audio_queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                logger.info(f"🎙️ [WHISPER PROCESSING] Transcribing chunk #{chunk_id} ({len(pcm_bytes)} bytes)...")
                stt_res = self.stt.transcribe_audio_bytes(pcm_bytes, suffix=".raw_pcm")
                
                if stt_res.get("success") and stt_res.get("text"):
                    raw_text = stt_res["text"].strip()
                    clean_text = self.rag.correct_speech_transcript(raw_text)
                    lat = stt_res.get("latency_ms", 0)

                    logger.info(f"✅ [TRANSCRIPTION RESULT #{chunk_id}] '{clean_text}' (Latency: {lat:.1f}ms)")
                    
                    now = time.time()
                    # Smart Thought Accumulator: If client continues thought within 2.5s, combine clauses into one complete sentence
                    if self.sentence_buffer and (now - self.last_chunk_time) < 2.5:
                        existing_text = " ".join(self.sentence_buffer).lower()
                        if clean_text.lower() not in existing_text:
                            self.sentence_buffer.append(clean_text)
                    else:
                        self.sentence_buffer = [clean_text]

                    self.last_chunk_time = now
                    full_sentence = " ".join(self.sentence_buffer).strip()
                    full_sentence = self.rag.correct_speech_transcript(full_sentence)

                    # 1. Always stream live transcript to UI
                    payload_transcription = {
                        "type": "transcription_complete",
                        "text": full_sentence,
                        "chunk_text": clean_text,
                        "stt_latency_ms": lat
                    }
                    if self.loop and self.loop.is_running():
                        asyncio.run_coroutine_threadsafe(self.broadcast_fn(payload_transcription), self.loop)

                    # 2. Check if the thought is mature enough for Strategic Intent Analysis
                    words = full_sentence.split()
                    sales_keywords = [
                        "price", "rate", "cost", "discount", "cheap", "expensive", "nda", "security",
                        "competitor", "other", "freelancer", "agency", "timeline", "delay", "deadline",
                        "deliver", "milestone", "refund", "contract", "scope", "kam", "paisa", "mehanga",
                        "less", "doing", "money", "budget", "offer", "charge"
                    ]
                    has_intent_keywords = any(kw in full_sentence.lower() for kw in sales_keywords)

                    # Only run strategy lookup if full thought has intent keywords or length >= 3 words
                    if (len(words) >= 3 or has_intent_keywords) and full_sentence != self.last_analyzed_sentence:
                        self.last_analyzed_sentence = full_sentence

                        # RAG & Intent Analysis on complete accumulated sentence
                        rag_res = self.rag.query(full_sentence)
                        intent_res = self.rag.analyze_intent(full_sentence)

                        if intent_res.get("is_match") and intent_res.get("recommended_pitch"):
                            logger.info(f"🎯 [STRATEGY DISPATCHED] Complete Thought: '{full_sentence}' -> Intent: {intent_res.get('intent_title')} | Q{rag_res.get('q_number')}")

                            payload_intent = {
                                "type": "intent_strategy_response",
                                "data": intent_res
                            }
                            payload_battlecard = {
                                "type": "battlecard_response",
                                "data": rag_res
                            }

                            if self.loop and self.loop.is_running():
                                asyncio.run_coroutine_threadsafe(self.broadcast_fn(payload_intent), self.loop)
                                asyncio.run_coroutine_threadsafe(self.broadcast_fn(payload_battlecard), self.loop)
                        else:
                            logger.debug(f"No battlecard matched for: '{full_sentence}'. Popup suppressed.")
                else:
                    logger.debug(f"Chunk #{chunk_id} contained no intelligible speech or silence.")

                self.audio_queue.task_done()
            except Exception as e:
                logger.error(f"Error in Whisper worker consumer: {e}")

desktop_listener = DesktopAudioListener(stt_engine, rag_engine, manager.broadcast)

# --- Request Models ---
class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 3

class IntentRequest(BaseModel):
    text: str

class ConfigUpdateRequest(BaseModel):
    min_relevance: Optional[float] = None
    llm_model: Optional[str] = None
    ollama_base_url: Optional[str] = None

# --- REST Endpoints ---

@app.get("/api/ping")
async def ping_check():
    """Lightweight ping endpoint for Chrome extension health checks."""
    return {"status": "pong", "time": time.time()}

@app.get("/api/health")
async def health_check():
    """Returns system status, Ollama connectivity, and knowledge base stats."""
    ollama_online = rag_engine.check_ollama()
    models = rag_engine.get_ollama_models() if ollama_online else []
    return {
        "status": "online",
        "ollama_online": ollama_online,
        "available_models": models,
        "active_model": rag_engine.llm_model,
        "knowledge_base_cards": len(rag_engine.documents),
        "vectorstore_ready": rag_engine.vectorstore is not None,
        "min_relevance": rag_engine.min_relevance,
        "whisper_model": stt_engine.model_name
    }

@app.post("/api/query")
async def process_query(req: QueryRequest):
    """Processes a text query through RAG pipeline and returns the strategy."""
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    
    result = await asyncio.to_thread(rag_engine.query, req.query, req.top_k or 3)
    return result

@app.post("/api/analyze-intent")
async def analyze_client_intent(req: IntentRequest):
    """Analyzes client text to identify intent, sentiment, and returns actionable strategy."""
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    
    result = await asyncio.to_thread(rag_engine.analyze_intent, req.text)
    return result

@app.post("/api/stt")
async def transcribe_audio(file: UploadFile = File(...)):
    """Receives an uploaded audio file (WAV/WebM) and transcribes using Whisper."""
    try:
        content = await file.read()
        suffix = os.path.splitext(file.filename)[1] if file.filename else ".wav"
        if not suffix:
            suffix = ".wav"
        result = await stt_engine.transcribe_async(content, suffix=suffix)
        return result
    except Exception as e:
        logger.error(f"STT endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/battlecards")
async def get_battlecards(q: Optional[str] = None):
    """Returns all knowledge base battlecards, optionally filtered by keyword."""
    cards = rag_engine.get_all_battlecards()
    if q and q.strip():
        query_lower = q.lower().strip()
        cards = [
            c for c in cards
            if query_lower in c["question"].lower()
            or query_lower in c["pitch"].lower()
            or query_lower in c["context"].lower()
            or str(c["q_number"]) == query_lower
        ]
    return {"total": len(cards), "battlecards": cards}

@app.get("/api/knowledge-status")
async def get_knowledge_status():
    """Returns metadata about the active custom or default sales playbook."""
    return rag_engine.get_knowledge_metadata()

@app.post("/api/upload-document")
async def upload_custom_document(file: UploadFile = File(...)):
    """
    Receives a custom sales document (PDF, DOCX, TXT, CSV),
    chunks it into strategy battlecards, computes vector embeddings, and activates it live.
    """
    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        
        # Max file size guard: 25 MB
        MAX_FILE_SIZE = 25 * 1024 * 1024
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail=f"File too large ({len(content)/(1024*1024):.1f} MB). Maximum supported size is 25 MB.")

        # Allowed extensions
        allowed_exts = {".pdf", ".docx", ".doc", ".txt", ".md", ".csv", ".json", ".log"}
        ext = os.path.splitext(file.filename or "")[1].lower()
        if ext not in allowed_exts:
            raise HTTPException(status_code=400, detail=f"Unsupported file format '{ext}'. Please upload PDF, DOCX, TXT, MD, or CSV.")
        
        result = await asyncio.to_thread(rag_engine.load_custom_document, content, file.filename or "uploaded_doc")
        
        # Broadcast real-time knowledge update to all connected UI clients & Chrome extension
        await manager.broadcast({
            "type": "knowledge_base_updated",
            "data": {
                "active_document": result["filename"],
                "total_chunks": result["total_chunks"],
                "uploaded_at": result["uploaded_at"],
                "strategies": rag_engine.get_all_battlecards()
            }
        })
        
        return result
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error processing custom document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")

@app.post("/api/reset-knowledge")
async def reset_knowledge_base():
    """Restores default 70 sales battlecards from zoom.pdf."""
    try:
        result = await asyncio.to_thread(rag_engine.reset_to_default_knowledge_base)
        await manager.broadcast({
            "type": "knowledge_base_updated",
            "data": {
                "active_document": result["active_document"],
                "total_chunks": result["total_chunks"],
                "is_custom": False,
                "strategies": rag_engine.get_all_battlecards()
            }
        })
        return result
    except Exception as e:
        logger.error(f"Error resetting knowledge base: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/config")
async def update_config(config: ConfigUpdateRequest):
    """Updates runtime configuration (e.g. minimum relevance threshold or model)."""
    if config.min_relevance is not None:
        rag_engine.min_relevance = max(0.0, min(1.0, config.min_relevance))
    if config.llm_model is not None:
        rag_engine.llm_model = config.llm_model
    if config.ollama_base_url is not None:
        rag_engine.ollama_base_url = config.ollama_base_url.rstrip("/")
    return {
        "success": True,
        "min_relevance": rag_engine.min_relevance,
        "llm_model": rag_engine.llm_model,
        "ollama_base_url": rag_engine.ollama_base_url
    }

# --- Autonomous Desktop Listener Lifecycle & Endpoints ---

@app.on_event("startup")
async def startup_event():
    """Auto-activates autonomous desktop WASAPI loopback audio listener."""
    loop = asyncio.get_running_loop()
    try:
        desktop_listener.start(loop)
    except Exception as e:
        logger.warning(f"Could not auto-start DesktopAudioListener: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanly stops background audio listener."""
    desktop_listener.stop()

@app.get("/api/desktop-listener/status")
async def get_desktop_listener_status():
    return {
        "running": desktop_listener.is_running,
        "device": desktop_listener.device_name
    }

@app.post("/api/desktop-listener/toggle")
async def toggle_desktop_listener():
    loop = asyncio.get_running_loop()
    if desktop_listener.is_running:
        desktop_listener.stop()
        return {"running": False, "message": "Desktop Audio Listener stopped"}
    else:
        desktop_listener.start(loop)
        return {"running": True, "message": f"Desktop Audio Listener active on {desktop_listener.device_name}"}

# --- WebSocket Gateway for Real-Time Streaming ---

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    # Conversational Rolling Sentence Memory & Utterance Accumulator
    sentence_buffer: List[str] = []
    last_chunk_time: float = 0.0
    last_analyzed_sentence: str = ""
    conversation_history: List[Dict[str, Any]] = []

    try:
        # Send initial welcome and state
        await websocket.send_json({
            "type": "system_status",
            "data": {
                "status": "ready",
                "total_cards": len(rag_engine.documents),
                "active_document": rag_engine.active_document_name,
                "is_custom": rag_engine.active_document_uploaded_at is not None,
                "ollama_online": rag_engine.check_ollama(),
                "model": rag_engine.llm_model
            }
        })

        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
            except Exception:
                continue

            msg_type = msg.get("type", "query")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong", "time": time.time()})

            elif msg_type == "state_change":
                # UI notifying stage e.g. listening / speaking
                state = msg.get("state", "idle")
                logger.info(f"Client state changed to: {state}")

            elif msg_type == "query":
                query_text = msg.get("text", "").strip()
                if not query_text:
                    continue

                stt_latency = msg.get("stt_latency_ms", 0)

                # 1. Notify UI: Searching Knowledge Base
                await websocket.send_json({
                    "type": "stage_update",
                    "stage": "searching",
                    "query": query_text
                })

                # 2. Execute RAG query in background thread
                rag_res = await asyncio.to_thread(rag_engine.query, query_text)
                
                if stt_latency > 0:
                    rag_res["stt_latency_ms"] = stt_latency
                    rag_res["total_latency_ms"] += stt_latency

                # 3. Broadcast final result back to UI
                await websocket.send_json({
                    "type": "battlecard_response",
                    "data": rag_res
                })

            elif msg_type == "analyze_intent":
                intent_text = msg.get("text", "").strip()
                if not intent_text:
                    continue

                await websocket.send_json({
                    "type": "stage_update",
                    "stage": "analyzing_intent",
                    "query": intent_text
                })

                intent_res = await asyncio.to_thread(rag_engine.analyze_intent, intent_text)

                await websocket.send_json({
                    "type": "intent_strategy_response",
                    "data": intent_res
                })

            elif msg_type == "audio_chunk":
                # Audio blob uploaded over WebSocket
                audio_b64 = msg.get("audio_base64", "")
                audio_format = msg.get("format", ".raw_pcm")
                if not audio_format.startswith("."):
                    audio_format = f".{audio_format}"

                if audio_b64:
                    try:
                        clean_b64 = re.sub(r'[^A-Za-z0-9+/=]', '', audio_b64.strip())
                        pad_needed = (4 - len(clean_b64) % 4) % 4
                        if pad_needed:
                            clean_b64 += '=' * pad_needed
                        raw_audio = base64.b64decode(clean_b64)
                        stt_res = await stt_engine.transcribe_async(raw_audio, suffix=audio_format)
                    except Exception as e:
                        logger.error(f"Error decoding or transcribing audio chunk: {e}")
                        stt_res = {"success": False, "error": str(e)}
                    
                    if stt_res.get("success") and stt_res.get("text"):
                        raw_fragment = stt_res["text"].strip()
                        # Apply instant AI contextual correction (e.g. 'what youtube' -> 'what will you do')
                        new_fragment = rag_engine.correct_speech_transcript(raw_fragment)
                        stt_lat = stt_res.get("latency_ms", 0)
                        now = time.time()

                        # Smart Rolling Sentence Memory:
                        # If client continues speaking within 1.0s natural pause, combine fragments into one complete thought
                        if sentence_buffer and (now - last_chunk_time) < 1.0:
                            # Avoid duplicate consecutive words
                            if new_fragment.lower() not in " ".join(sentence_buffer).lower():
                                sentence_buffer.append(new_fragment)
                        else:
                            # Reset for fresh sentence
                            sentence_buffer = [new_fragment]

                        last_chunk_time = now
                        full_sentence = " ".join(sentence_buffer).strip()

                        # Double check full accumulated sentence with contextual correction
                        full_sentence = rag_engine.correct_speech_transcript(full_sentence)

                        logger.info(f"⚡ Clean Client Thought (Memory: {len(sentence_buffer)} chunks): '{full_sentence}'")
                        
                        # 1. Send live accumulated clean sentence to UI
                        await websocket.send_json({
                            "type": "transcription_complete",
                            "text": full_sentence,
                            "chunk_text": new_fragment,
                            "stt_latency_ms": stt_lat
                        })

                        # 2. Run RAG & Intent Analysis on the COMPLETE sentence
                        if full_sentence and full_sentence != last_analyzed_sentence:
                            last_analyzed_sentence = full_sentence

                            rag_task = asyncio.to_thread(rag_engine.query, full_sentence)
                            intent_task = asyncio.to_thread(rag_engine.analyze_intent, full_sentence)
                            rag_res, intent_res = await asyncio.gather(rag_task, intent_task)

                            rag_res["stt_latency_ms"] = stt_lat
                            rag_res["total_latency_ms"] += stt_lat

                            # Save to session conversation memory
                            conversation_history.append({
                                "client_sentence": full_sentence,
                                "intent": intent_res.get("intent_title"),
                                "matched_q": rag_res.get("q_number")
                            })

                            # Only dispatch strategic popup if a real battlecard is matched
                            if intent_res.get("is_match") and intent_res.get("recommended_pitch"):
                                # Send Intent & Psychology Strategy Response
                                await websocket.send_json({
                                    "type": "intent_strategy_response",
                                    "data": intent_res
                                })

                                # Send Battlecard Response
                                await websocket.send_json({
                                    "type": "battlecard_response",
                                    "data": rag_res
                                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# --- Mount Static Frontend ---
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def serve_index():
    """Serves the main application page."""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>Sales Assistant UI Initializing...</h1>")

if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    print("==================================================================")
    print(" [READY] REAL-TIME LOCAL AI SALES ASSISTANT (VOICE RAG CO-PILOT) ")
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    print(f" Server running on: http://{host}:{port}")
    print(" Knowledge Base loaded: 70 Q&A Battlecards from zoom.pdf")
    print("==================================================================")
    uvicorn.run("server:app", host=host, port=port, log_level="info")

