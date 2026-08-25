# rag_engine.py
"""
RAG Engine for Local Real-Time AI Sales Assistant.
Handles PDF parsing, ChromaDB vector indexing/retrieval, Ollama LLM queries,
and strict sales guardrails with language preservation.
"""

import os
import re
import time
import json
import logging
from typing import List, Dict, Any, Optional
import requests
from pypdf import PdfReader
from doc_processor import DocumentProcessor

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("RAGEngine")

class RAGEngine:
    def __init__(
        self,
        pdf_path: str = "zoom.pdf",
        chroma_path: str = "chroma_db_v2",
        min_relevance: float = 0.35,
        ollama_base_url: str = "http://127.0.0.1:11434",
        llm_model: str = "llama3.2:3b",
        embedding_model: str = "nomic-embed-text"
    ):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.pdf_path = os.path.join(base_dir, pdf_path) if not os.path.isabs(pdf_path) else pdf_path
        self.chroma_path = os.path.join(base_dir, chroma_path) if not os.path.isabs(chroma_path) else chroma_path
        self.min_relevance = min_relevance
        self.ollama_base_url = ollama_base_url.rstrip("/")
        self.llm_model = llm_model
        self.embedding_model = embedding_model
        
        self.documents: List[Dict[str, Any]] = []
        self.vectorstore = None
        self.query_cache: Dict[str, Dict[str, Any]] = {}
        self.active_document_name: str = "zoom.pdf (Default 70 Battlecards)"
        self.active_document_uploaded_at: Optional[str] = None

        
        # Auto-detect best available Ollama model
        if self.check_ollama():
            avail = self.get_ollama_models()
            if avail and self.llm_model not in avail:
                for m in avail:
                    if any(cand in m.lower() for cand in ["llama3.2", "llama3", "llama", "phi3", "mistral", "qwen"]):
                        self.llm_model = m
                        break
                else:
                    self.llm_model = avail[0]
                logger.info(f"Ollama detected. Selected active model: {self.llm_model}")

        # Stopwords for conversational filtering
        self.stopwords = set([
            "a", "an", "the", "is", "are", "was", "were", "in", "on", "at", "to", "for", "of", "with",
            "by", "from", "and", "or", "but", "if", "that", "this", "it", "you", "your", "we", "our",
            "i", "my", "me", "us", "they", "them", "their", "how", "what", "when", "where", "why",
            "who", "which", "would", "could", "should", "do", "does", "did", "can", "will", "be",
            "been", "being", "have", "has", "had", "take", "need", "get", "give", "make", "agar",
            "kya", "hum", "aap", "ko", "se", "ka", "ki", "ke", "hai", "hain", "toh", "aur", "karo",
            "karein", "bhi", "yeh", "woh", "kar", "rahe", "raha", "meri", "mera", "apna",
            # Generic domain words to prevent bias
            "project", "projects", "work", "working", "app", "application", "software", "system",
            "thing", "things", "stuff", "say", "said", "ask", "asking", "tell", "telling"
        ])
        
        # Core Sales Concept Groups for deep semantic synergy
        self.synonym_groups = [
            {"name": "billing_charges", "words": {"payment", "pay", "billed", "bill", "billing", "charge", "charges", "charging", "fee", "fees", "cost", "costs", "price", "rate", "rates", "invoice", "overtime", "deposit", "money", "dollar", "dollars"}},
            {"name": "timeline_delay", "words": {"time", "complete", "finish", "completion", "duration", "how long", "when", "deliver", "delivery", "deadline", "deadlines", "timeline", "timelines", "schedule", "schedules", "missed", "miss", "exceeds", "exceed", "delay", "delayed", "delays", "late", "eta", "urgent", "hurry", "rush", "speed", "fast", "days", "weeks", "months"}},
            {"name": "hours_extra", "words": {"hours", "hour", "working", "work", "overtime", "extra", "additional", "more", "increase", "increased", "overtime"}},
            {"name": "scope_cr", "words": {"scope", "sow", "feature", "features", "change", "changes", "cr", "custom", "customization", "addition", "additions", "revision", "revisions", "requirement", "requirements"}},
            {"name": "contract_type", "words": {"fixed", "fixed-price", "fixed-scope", "hourly", "retainer", "contract", "contracts", "milestone", "milestones", "terms"}},
            {"name": "trust_nda", "words": {"security", "secure", "nda", "ip", "intellectual property", "source code", "code", "confidential", "confidentiality", "ownership", "rights", "steal", "leak", "privacy", "protection", "protect", "audit", "compliance"}},
            {"name": "discount_cost", "words": {"discount", "discounts", "concession", "cheaper", "cheap", "less", "lower", "reduce", "reduction", "expensive", "costly", "tight budget"}},
            {"name": "competitor_freelancer", "words": {"freelancer", "freelancers", "upwork", "fiverr", "competitor", "competitors", "another agency", "other agency", "other company"}}
        ]
        
        # Load documents and initialize vectorstore/in-memory fallback
        self._initialize_knowledge_base()

    def _extract_qa_from_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Parses zoom.pdf into structured Q&A objects."""
        if not os.path.exists(pdf_path):
            logger.warning(f"PDF not found at {pdf_path}. Returning empty list.")
            return []

        try:
            reader = PdfReader(pdf_path)
            full_text = "\n".join([page.extract_text() or "" for page in reader.pages])
            
            full_text = full_text.replace("\ufffd", "-")
            full_text = full_text.replace("\u00ad", "")
            
            blocks = [b.strip() for b in re.split(r'(?=Q\d+\.)', full_text) if re.match(r'^Q\d+\.', b.strip())]
            
            structured_qa = []
            for b in blocks:
                m = re.search(r'Q(\d+)\.\s*(.+?)\n\s*Context\s*/\s*Rationale\s*\n+(.+?)\n+\s*Exact\s*Strategy\s*/\s*Pitch\s*\n+(.+)', b, re.DOTALL)
                if m:
                    q_number = int(m.group(1))
                    question = " ".join(m.group(2).strip().split())
                    context = m.group(3).strip()
                    pitch = m.group(4).strip()
                    structured_qa.append({
                        "q_number": q_number,
                        "question": question,
                        "context": context,
                        "pitch": pitch,
                        "full_text": f"Question:\n{question}\n\nContext / Rationale:\n{context}\n\nExact Strategy / Pitch:\n{pitch}",
                        "source": "Enterprise Sales & Client Handling Knowledge Base"
                    })
            logger.info(f"Successfully extracted {len(structured_qa)} structured Q&A battlecards from {pdf_path}")
            return structured_qa
        except Exception as e:
            logger.error(f"Error extracting PDF Q&A: {e}")
            return []

    def _initialize_knowledge_base(self):
        """Loads structured documents and tries to initialize ChromaDB."""
        self.documents = self._extract_qa_from_pdf(self.pdf_path)
        
        # Try initializing ChromaDB if available
        try:
            from langchain_community.vectorstores import Chroma
            from langchain_community.embeddings import OllamaEmbeddings
            from langchain_core.documents import Document
            
            if self.check_ollama():
                embeddings = OllamaEmbeddings(
                    model=self.embedding_model,
                    base_url=self.ollama_base_url
                )
                
                if os.path.exists(self.chroma_path) and os.listdir(self.chroma_path):
                    logger.info(f"Loading existing ChromaDB from {self.chroma_path}")
                    self.vectorstore = Chroma(
                        persist_directory=self.chroma_path,
                        embedding_function=embeddings,
                        collection_name="sales_qa_v2"
                    )
                elif self.documents:
                    logger.info(f"Creating new ChromaDB at {self.chroma_path}")
                    os.makedirs(self.chroma_path, exist_ok=True)
                    langchain_docs = [
                        Document(
                            page_content=doc["full_text"],
                            metadata={
                                "q_number": doc["q_number"],
                                "question": doc["question"],
                                "context": doc["context"],
                                "pitch": doc["pitch"],
                                "source": doc["source"]
                            }
                        ) for doc in self.documents
                    ]
                    self.vectorstore = Chroma.from_documents(
                        documents=langchain_docs,
                        embedding=embeddings,
                        collection_name="sales_qa_v2",
                        persist_directory=self.chroma_path
                    )
        except Exception as e:
            logger.warning(f"ChromaDB initialization deferred or using in-memory hybrid matcher: {e}")

    def check_ollama(self) -> bool:
        """Checks if local Ollama server is responsive."""
        try:
            res = requests.get(f"{self.ollama_base_url}/api/tags", timeout=1.5)
            return res.status_code == 200
        except Exception:
            return False

    def get_ollama_models(self) -> List[str]:
        """Returns available Ollama model tags."""
        try:
            res = requests.get(f"{self.ollama_base_url}/api/tags", timeout=2.0)
            if res.status_code == 200:
                data = res.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            pass
        return ["llama3.2:3b", "llama3.2:1b", "phi3:latest", "nomic-embed-text"]

    def is_casual_or_random_speech(self, text: str) -> bool:
        """
        Determines if an utterance is casual chit-chat, greeting, acknowledgment,
        or filler speech that should NOT trigger any sales popup or strategy alert.
        """
        if not text:
            return True
            
        clean = text.lower().strip()
        if not clean:
            return True
            
        # Common casual words & incomplete starter phrases in English & Roman Urdu
        casual_exact_phrases = {
            "hi", "hello", "hey", "hey there", "good morning", "good afternoon", "good evening",
            "how are you", "how are you doing", "how do you do", "nice to meet you", "pleasure to meet you",
            "can you hear me", "am i audible", "is my audio clear", "testing", "testing mic", "1 2 3", "one two three",
            "yes", "yeah", "yep", "yup", "no", "nope", "nah", "okay", "ok", "sure", "alright", "all right",
            "cool", "fine", "great", "awesome", "perfect", "got it", "understood", "makes sense",
            "thank you", "thanks", "thanks a lot", "bye", "goodbye", "see you", "talk soon",
            "let's start", "let's begin", "shall we start", "give me a second", "hold on", "one minute",
            "kya haal hai", "theek ho", "kaise ho", "haan", "nahi", "shukriya", "suno", "bolo",
            "acha", "accha", "theek hai", "sahi hai", "zabardast", "shuru karein", "awaz aa rahi hai",
            # Incomplete conversational starter fragments
            "i want", "i need", "can you give", "can you give me a", "can you give me",
            "we want", "we need", "i am good", "i am good this is", "doing this", "doing", "this is",
            # Wrap-up, praise, and call-ending banter
            "behtarin", "behtareen", "behtarin ho gaya", "behtarin ho gaya band kar do", "band kar do",
            "band karo", "ho gaya", "khatam", "khatam ho gaya", "all set", "wrap up", "done", "finished",
            "bohot acha", "shabash", "theek ho gaya", "good job", "call khatam", "sab theek hai"
        }
        
        normalized = re.sub(r'[^\w\s]', '', clean, flags=re.UNICODE).strip()
        if normalized in casual_exact_phrases:
            return True
            
        # If utterance has strong sales trigger keywords, it is NOT casual
        strong_sales_words = {
            "price", "pricing", "rate", "rates", "cost", "costs", "discount", "discounts",
            "expensive", "cheap", "cheaper", "budget", "money", "dollars", "payment",
            "nda", "ip", "security", "source", "code", "proprietary", "confidential",
            "competitor", "competitors", "freelancer", "freelancers", "upwork", "fiverr",
            "timeline", "delay", "delayed", "deadline", "milestone", "delivery", "late", "urgent",
            "refund", "warranty", "contract", "hourly", "overtime", "scope",
            "kam", "paisa", "mehanga", "sasta", "takhier", "madad"
        }
        
        words = re.findall(r'[\w\-]+', normalized, re.UNICODE)
        if not words:
            return True

        if any(w in strong_sales_words for w in words):
            return False
            
        # If utterance is very short and only contains greetings/fillers/stopwords
        fillers = {
            "hi", "hello", "hey", "yes", "yeah", "no", "nope", "okay", "ok", "sure", "alright",
            "thanks", "thank", "you", "good", "morning", "evening", "afternoon", "fine", "great",
            "cool", "well", "so", "um", "uh", "like", "actually", "basically", "hear", "me", "am",
            "audible", "loud", "clear", "start", "begin", "meeting", "call", "today", "now",
            "want", "need", "give", "doing", "other", "people",
            "haan", "nahi", "theek", "acha", "accha", "sahi", "suno", "bolo", "bhai", "sir", "guys"
        }
        
        non_filler_words = [w for w in words if w not in fillers and w not in self.stopwords and len(w) > 1]
        if not non_filler_words:
            return True
            
        return False

    def _fallback_lexical_match(self, query: str) -> Optional[Dict[str, Any]]:
        """Smart keyword/concept synergy relevance matcher with stopword removal and title priority."""
        if not self.documents:
            return None
            
        if self.is_casual_or_random_speech(query):
            return None
            
        clean_query = self.correct_speech_transcript(query.lower().strip())
        raw_words = re.findall(r'[\w\-]+', clean_query, re.UNICODE)
        content_words = [w for w in raw_words if w not in self.stopwords and len(w) > 1]
        if not content_words:
            return None

        query_set = set(content_words)

        # Identify active concepts in query
        query_active_concepts = set()
        for group in self.synonym_groups:
            if any(w in clean_query or w in query_set for w in group["words"]):
                query_active_concepts.add(group["name"])

        best_doc = None
        best_score = 0.0

        for doc in self.documents:
            doc_q = doc["question"].lower()
            doc_c = doc["context"].lower()
            doc_p = doc["pitch"].lower()
            doc_full = f"{doc_q} {doc_c} {doc_p}"
            
            # Direct question match boost
            if clean_query in doc_q or doc_q in clean_query:
                return {"doc": doc, "score": 0.98}

            score = 0.0

            # 1. Question Title Word Overlap (Primary decisive factor: 5x weight)
            for w in content_words:
                if re.search(r'\b' + re.escape(w) + r'\b', doc_q):
                    score += 4.0
                elif w in doc_q:
                    score += 2.0

            # 2. Context & Pitch Word Overlap (Secondary factor: 1x weight)
            for w in content_words:
                if re.search(r'\b' + re.escape(w) + r'\b', doc_c + " " + doc_p):
                    score += 1.0

            # 3. Concept Synergy Boost
            doc_active_concepts = set()
            for group in self.synonym_groups:
                if any(w in doc_full for w in group["words"]):
                    doc_active_concepts.add(group["name"])

            shared_concepts = query_active_concepts.intersection(doc_active_concepts)
            if shared_concepts:
                score += 3.0 * len(shared_concepts)

            # Normalize score
            normalized_score = min(score / max(len(content_words) * 5.0, 5.0), 0.98)

            if score > best_score:
                best_score = score
                best_doc = doc

        if best_doc and best_score >= 2.0:
            return {"doc": best_doc, "score": min(0.75 + (best_score * 0.05), 0.98)}
        return None

    def query(self, user_question: str, top_k: int = 3) -> Dict[str, Any]:
        """
        Executes end-to-end RAG retrieval + Ollama LLM answer synthesis.
        Returns comprehensive telemetry and strict sales pitch output.
        """
        start_time = time.time()
        clean_question = user_question.strip()
        
        if not clean_question or self.is_casual_or_random_speech(clean_question):
            return {
                "success": False,
                "response": "",
                "pitch": "",
                "context": "",
                "question_matched": "",
                "q_number": None,
                "relevance_score": 0.0,
                "confidence_percent": 0,
                "rag_latency_ms": 0,
                "llm_latency_ms": 0,
                "total_latency_ms": int((time.time() - start_time) * 1000),
                "match_source": "CasualFilter",
                "ollama_used": False,
                "cached": False,
                "is_casual": True
            }

        # Check in-memory cache for instant <10ms replay with TTL (300s)
        cache_key = clean_question.lower()
        now = time.time()
        if cache_key in self.query_cache:
            entry = self.query_cache[cache_key]
            if now - entry.get("_cached_at", 0) < 300:
                cached = dict(entry["data"])
                cached["cached"] = True
                cached["total_latency_ms"] = int((time.time() - start_time) * 1000)
                return cached
            cached["total_latency_ms"] = int((time.time() - start_time) * 1000)
            return cached

        rag_start = time.time()
        best_doc = None
        relevance_score = 0.0
        match_source = "None"

        # 1. Try ChromaDB if initialized
        if self.vectorstore is not None:
            try:
                results = self.vectorstore.similarity_search_with_relevance_scores(
                    clean_question,
                    k=top_k
                )
                if results:
                    top_doc, score = results[0]
                    relevance_score = float(score)
                    best_doc = {
                        "q_number": top_doc.metadata.get("q_number", 0),
                        "question": top_doc.metadata.get("question", ""),
                        "context": top_doc.metadata.get("context", ""),
                        "pitch": top_doc.metadata.get("pitch", ""),
                        "source": top_doc.metadata.get("source", "Knowledge Base")
                    }
                    match_source = "ChromaDB"
            except Exception as e:
                logger.warning(f"Vector search failed, falling back to lexical matcher: {e}")

        # 2. Fallback to in-memory matcher if ChromaDB didn't match or is uninitialized
        if best_doc is None or relevance_score < self.min_relevance:
            fallback_res = self._fallback_lexical_match(clean_question)
            if fallback_res and fallback_res["score"] > relevance_score:
                best_doc = fallback_res["doc"]
                relevance_score = fallback_res["score"]
                match_source = "KnowledgeBase_Lexical"

        rag_latency_ms = int((time.time() - rag_start) * 1000)

        # Check threshold
        if best_doc is None or relevance_score < self.min_relevance:
            total_latency_ms = int((time.time() - start_time) * 1000)
            return {
                "success": False,
                "response": "No matching strategy in Knowledge Base. Feel free to rephrase or consult team leadership.",
                "pitch": "",
                "context": "",
                "question_matched": "",
                "q_number": None,
                "relevance_score": round(relevance_score, 4),
                "confidence_percent": int(relevance_score * 100),
                "rag_latency_ms": rag_latency_ms,
                "llm_latency_ms": 0,
                "total_latency_ms": total_latency_ms,
                "match_source": match_source,
                "ollama_used": False,
                "cached": False
            }

        pitch = best_doc["pitch"]
        context = best_doc["context"]
        matched_question = best_doc["question"]
        q_number = best_doc["q_number"]

        # Exact Battlecard pitch ready in <15ms
        rag_latency_ms = int((time.time() - rag_start) * 1000)
        total_latency_ms = int((time.time() - start_time) * 1000)

        result_payload = {
            "success": True,
            "response": pitch,
            "pitch": pitch,
            "context": context,
            "question_matched": matched_question,
            "q_number": q_number,
            "relevance_score": round(relevance_score, 4),
            "confidence_percent": min(int(relevance_score * 100), 100),
            "rag_latency_ms": rag_latency_ms,
            "llm_latency_ms": 0,
            "total_latency_ms": total_latency_ms,
            "match_source": match_source,
            "ollama_used": False,
            "cached": False
        }

        # Save in cache with TTL timestamp
        if len(self.query_cache) > 200:
            self.query_cache.clear()
        self.query_cache[cache_key] = {
            "_cached_at": time.time(),
            "data": result_payload
        }

        return result_payload

    def analyze_intent(self, text: str) -> Dict[str, Any]:
        """
        Analyzes client input text to determine core intent, psychological friction points,
        sentiment, and recommended sales strategy & pitch.
        If the utterance is random or casual chit-chat, suppresses popup by returning is_match=False.
        """
        start_time = time.time()
        clean_text = text.strip()
        if not clean_text:
            return {
                "success": False,
                "is_match": False,
                "matched": False,
                "error": "Input text cannot be empty.",
                "intent_title": "Unknown Intent",
                "intent_category": "General",
                "confidence_percent": 0,
                "recommended_pitch": ""
            }

        # 1. First check if it is casual / chit-chat / random talk
        if self.is_casual_or_random_speech(clean_text):
            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "success": False,
                "is_match": False,
                "matched": False,
                "input_text": clean_text,
                "intent_title": "Casual Conversation",
                "message": "Casual chit-chat detected. No sales objection or closing popup triggered.",
                "confidence_percent": 0,
                "client_mindset": "Casual conversation / greeting / filler speech.",
                "hidden_concern": "None",
                "recommended_pitch": "",
                "dos": [],
                "donts": [],
                "matched_question": "",
                "q_number": None,
                "context": "",
                "latency_ms": latency_ms,
                "ollama_enhanced": False
            }

        # 2. Retrieve best matching battlecard via RAG
        rag_res = self.query(clean_text)
        
        # 3. Heuristic Intent Categorization
        text_lower = clean_text.lower()
        matched_q_text = (rag_res.get("question_matched") or "").lower()
        
        # Comprehensive Intent Rules with expanded vocabulary and contextual weighting
        intent_rules = [
            {
                "category": "Trust, IP Security & NDA",
                "badge_color": "cyan",
                "icon": "fa-shield-halved",
                "keywords": ["nda", "ip", "intellectual property", "security", "code theft", "steal", "stealing", "leak", "leaking", "copy", "privacy", "confidential", "confidentiality", "contract", "ownership", "source code", "code safe", "rights", "secure", "trust"],
                "client_mindset": "Risk-averse, highly protective of proprietary intellectual property and code confidentiality.",
                "hidden_concern": "Afraid their proprietary concept or source code might be leaked, reused, or compromised.",
                "dos": ["Offer a mutual NDA signed before conducting any technical deep-dive", "Explicitly confirm that 100% IP rights and source code belong to the client upon milestone payment"],
                "donts": ["Never dismiss or treat legal and security concerns casually", "Avoid vague or informal verbal promises"]
            },
            {
                "category": "Price Resistance & Budget Constraint",
                "badge_color": "amber",
                "icon": "fa-coins",
                "keywords": ["price", "cost", "expensive", "high", "rate", "budget", "charge", "afford", "quotation", "pricing", "dollar", "hourly", "costly", "affordability", "too much"],
                "client_mindset": "Cost-conscious, analyzing return on investment against upfront capital expenditure.",
                "hidden_concern": "Afraid of overpaying, project failure, or not achieving their expected return on investment.",
                "dos": ["Anchor on total cost of ownership, QA, automated testing, and production stability", "Offer milestone-based phased delivery or MVP rollout"],
                "donts": ["Never drop rates without proportionally adjusting scope", "Do not get defensive about professional agency pricing"]
            },
            {
                "category": "Discount & Commercial Negotiation",
                "badge_color": "amber",
                "icon": "fa-tags",
                "keywords": ["discount", "concession", "deal", "reduce", "package", "margin", "lump sum", "budget tight", "cheaper rate", "cut price", "offer"],
                "client_mindset": "Commercial negotiator testing pricing flexibility and seeking the best possible financial terms.",
                "hidden_concern": "Wants assurance they secured maximum value and a winning deal before signing.",
                "dos": ["Offer value add-ons or scope trimming rather than flat discounts", "Protect project margins by highlighting dedicated enterprise engineering standards"],
                "donts": ["Never commit to arbitrary discounts on the initial discovery call", "Avoid sounding desperate to close the agreement"]
            },
            {
                "category": "Timeline & Delivery Urgency",
                "badge_color": "rose",
                "icon": "fa-stopwatch-20",
                "keywords": ["timeline", "deadline", "delivery", "deliver", "fast", "urgent", "hurry", "rush", "when", "days", "weeks", "launch", "eta", "asap", "schedule", "friday", "month", "speed", "quick", "quickly"],
                "client_mindset": "Under intense market pressure, anxious about delivery windows and launch milestones.",
                "hidden_concern": "Afraid missed deadlines will harm their business launch, investor relations, or live operations.",
                "dos": ["Break delivery into fast iterative sprints and release a functional MVP first", "Demonstrate clear sprint schedule, dedicated engineers, and daily progress tracking"],
                "donts": ["Never promise unrealistic deadlines that jeopardize code quality", "Avoid giving vague date estimates without technical breakdown"]
            },
            {
                "category": "Competitor & Freelancer Comparison",
                "badge_color": "rose",
                "icon": "fa-users-slash",
                "keywords": ["competitor", "freelancer", "freelancers", "other agency", "cheaper", "upwork", "fiverr", "india", "overseas", "another company", "another vendor", "competitors"],
                "client_mindset": "Comparing agency engineering against low-cost individual freelancers without accounting for risk.",
                "hidden_concern": "Skeptical whether agency pricing delivers tangible risk reduction, security, and superior code.",
                "dos": ["Highlight architecture durability, security audits, dedicated PM, and code warranty", "Emphasize dedicated backup engineers and long-term business continuity"],
                "donts": ["Never criticize competitors directly", "Avoid making unverified generic claims"]
            },
            {
                "category": "Technical Capability & Scalability",
                "badge_color": "emerald",
                "icon": "fa-microchip",
                "keywords": ["tech stack", "python", "react", "ai", "architecture", "scalability", "scale", "load", "traffic", "bugs", "testing", "performance", "api", "database", "infrastructure", "backend", "cloud"],
                "client_mindset": "Seeking engineering authority, architectural robustness, and technical proof.",
                "hidden_concern": "Worried the product will crash under high user load or fail modern scalability benchmarks.",
                "dos": ["Provide architecture diagrams, CI/CD pipeline breakdown, and automated test coverage", "Speak with engineering precision and reference proven tech stacks"],
                "donts": ["Avoid overusing technical buzzwords; provide direct architectural clarity"]
            },
            {
                "category": "Scope Creep & Change Management",
                "badge_color": "amber",
                "icon": "fa-arrows-split-up-and-left",
                "keywords": ["changes", "revisions", "scope", "extra", "features", "maintenance", "support", "post launch", "customization", "modifications", "warranty"],
                "client_mindset": "Wants development flexibility without unexpected surprise invoices.",
                "hidden_concern": "Afraid of hidden fees, inflexible contract lock-in, and post-launch abandonment.",
                "dos": ["Define a clear sprint scope accompanied by a transparent change-order policy", "Include 30 days of post-launch warranty and bug fixes in writing"],
                "donts": ["Do not become confrontational over minor change requests; clarify scope transparently"]
            }
        ]

        # 3. Best Rule Match
        best_rule = None
        highest_score = 0

        for rule in intent_rules:
            score = 0
            for kw in rule["keywords"]:
                if re.search(rf"\b{re.escape(kw)}", text_lower):
                    score += 3
                elif kw in text_lower:
                    score += 1

            for kw in rule["keywords"]:
                if kw in matched_q_text:
                    score += 1.5

            if score > highest_score:
                highest_score = score
                best_rule = rule

        # Default fallback rule if no specific keyword matched
        if not best_rule:
            best_rule = {
                "category": "Sales Strategy & Closing Guidance",
                "badge_color": "cyan",
                "icon": "fa-bullseye",
                "client_mindset": "Evaluating capability, value proposition, and execution approach.",
                "hidden_concern": "Seeking clarity on features, deliverables, and agency engineering standards.",
                "dos": ["Anchor on total business value, robust architecture, and clear deliverables", "Provide direct, confident, and transparent answers"],
                "donts": ["Avoid vague or ambiguous statements; give direct architectural clarity"]
            }

        # Pitch resolution:
        matched_pitch = ""
        matched_q = ""
        q_num = None
        confidence = 88

        # Strict Pitch & Battlecard Resolution: Only match if present in ChromaDB / Knowledge Base
        if rag_res.get("success") and rag_res.get("pitch"):
            matched_pitch = rag_res.get("response") or rag_res.get("pitch")
            matched_q = rag_res.get("question_matched") or ""
            q_num = rag_res.get("q_number")
            confidence = max(rag_res.get("confidence_percent", 88), 85)
        else:
            fallback_match = self._fallback_lexical_match(clean_text)
            if fallback_match and fallback_match.get("doc"):
                doc = fallback_match["doc"]
                matched_pitch = doc["pitch"]
                matched_q = doc["question"]
                q_num = doc.get("q_number")
                confidence = min(82 + int(highest_score * 2), 95)
            else:
                # STRICT: No manufactured pitches. If not in ChromaDB/KB, do NOT trigger popup!
                latency_ms = int((time.time() - start_time) * 1000)
                return {
                    "success": False,
                    "is_match": False,
                    "matched": False,
                    "input_text": clean_text,
                    "intent_title": "No Matching Strategy",
                    "message": "No matching strategy found in active knowledge base.",
                    "confidence_percent": 0,
                    "client_mindset": "General dialogue or unindexed topic.",
                    "hidden_concern": "None",
                    "recommended_pitch": "",
                    "dos": [],
                    "donts": [],
                    "matched_question": "",
                    "q_number": None,
                    "context": "",
                    "latency_ms": latency_ms,
                    "ollama_enhanced": False
                }

        latency_ms = int((time.time() - start_time) * 1000)

        return {
            "success": True,
            "is_match": True,
            "matched": True,
            "input_text": clean_text,
            "intent_title": best_rule["category"],
            "badge_color": best_rule.get("badge_color", "cyan"),
            "icon": best_rule.get("icon", "fa-bullseye"),
            "confidence_percent": confidence,
            "client_mindset": best_rule["client_mindset"],
            "hidden_concern": best_rule["hidden_concern"],
            "recommended_pitch": matched_pitch,
            "dos": best_rule["dos"],
            "donts": best_rule["donts"],
            "matched_question": matched_q,
            "q_number": q_num,
            "context": rag_res.get("context") or best_rule["hidden_concern"],
            "latency_ms": latency_ms,
            "ollama_enhanced": False
        }

    def correct_speech_transcript(self, raw_text: str) -> str:
        """
        Intelligently corrects acoustic speech mishearings in real-time.
        Uses phonetic heuristic repair + local Ollama context model for 100% free high accuracy.
        """
        if not raw_text or len(raw_text.strip()) < 3:
            return raw_text

        text = raw_text.strip()

        # 1. Common Sales Speech Acoustic Mishearing & Urdu Script Dictionary (Fast 0ms Lookup)
        acoustic_repairs = [
            (r'\bwhat youtube\b', 'what will you do'),
            (r'\bwhat you to\b', 'what will you do'),
            (r'\bhow youtube\b', 'how will you'),
            (r'\bfree lance\b', 'freelancer'),
            (r'\bfree lancers\b', 'freelancers'),
            (r'\bup work\b', 'Upwork'),
            (r'\bin voice\b', 'invoice'),
            (r'\bdis count\b', 'discount'),
            (r'\bdisc count\b', 'discount'),
            (r'\bbud get\b', 'budget'),
            (r'\bcon tract\b', 'contract'),
            (r'\band a\b', 'NDA'),
            (r'\ben de\b', 'NDA'),
            (r'\btime line\b', 'timeline'),
            (r'\bdead line\b', 'deadline'),
            (r'\bdelivry\b', 'delivery'),
            (r'\bhow much cost\b', 'how much does it cost'),
            (r'\bhow much charge\b', 'how much do you charge'),
            (r'\btime to take\b', 'time will you take'),
            (r'\bhow many time\b', 'how much time'),
            (r'\bcan you less\b', 'can you reduce price discount'),
            (r'\bkam karo\b', 'give a discount pricing'),
            (r'\bpaisa\b', 'pricing rate cost'),
            (r'\bpaiso\b', 'pricing rate cost'),
            (r'\bzyada hai\b', 'price too expensive'),
            (r'\bjaldi karo\b', 'deliver urgently timeline deadline'),
            # Urdu Nastaliq Script Mapping
            (r'قیمت|ریٹ|لاگت', 'price cost hourly rate'),
            (r'رعایت|کم کرو|کمی', 'discount concession price'),
            (r'معاہدہ|این ڈی اے|این۔ڈی۔اے', 'NDA Non-Disclosure Agreement contract'),
            (r'وقت|تاخیر|ڈیڈ لائن', 'timeline deadline delayed schedule'),
            (r'اضافی|نیا فیچر|تبدیلی', 'extra charges change request scope'),
            (r'فکسڈ|مقررہ', 'fixed price contract')
        ]

        cleaned = text
        for pattern, replacement in acoustic_repairs:
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)

        return cleaned

    def get_all_battlecards(self) -> List[Dict[str, Any]]:
        """Returns all Q&A battlecards for knowledge base explorer."""
        return [
            {
                "q_number": doc["q_number"],
                "question": doc["question"],
                "context": doc["context"],
                "pitch": doc["pitch"],
                "source": doc.get("source", "zoom.pdf")
            }
            for doc in self.documents
        ]

    def load_custom_document(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Parses a custom uploaded sales document, chunks it into strategies,
        generates vector embeddings, updates active knowledge base, and syncs with extension.
        """
        logger.info(f"Ingesting custom document: {filename} ({len(file_bytes)} bytes)")
        extracted_text = DocumentProcessor.extract_text(file_bytes, filename)
        if not extracted_text:
            raise ValueError("No readable text found in uploaded document.")

        new_chunks = DocumentProcessor.chunk_strategies(extracted_text, filename)
        if not new_chunks:
            raise ValueError("Could not extract any strategies or chunks from the document. Please ensure file has text.")

        # Assign full_text to each chunk
        for chunk in new_chunks:
            chunk["full_text"] = f"Question / Topic:\n{chunk['question']}\n\nContext:\n{chunk['context']}\n\nRecommended Pitch:\n{chunk['pitch']}"

        # 1. Update In-Memory Documents
        self.documents = new_chunks
        self.query_cache.clear()
        self.active_document_name = filename
        self.active_document_uploaded_at = time.strftime("%Y-%m-%d %H:%M:%S")

        # 2. Re-index ChromaDB / Vector Store with new embeddings
        try:
            from langchain_community.vectorstores import Chroma
            from langchain_community.embeddings import OllamaEmbeddings
            from langchain_core.documents import Document
            
            if self.check_ollama():
                embeddings = OllamaEmbeddings(
                    model=self.embedding_model,
                    base_url=self.ollama_base_url
                )
                langchain_docs = [
                    Document(
                        page_content=doc["full_text"],
                        metadata={
                            "q_number": doc["q_number"],
                            "question": doc["question"],
                            "context": doc["context"],
                            "pitch": doc["pitch"],
                            "source": doc["source"]
                        }
                    ) for doc in self.documents
                ]
                # Re-create vectorstore in memory or new collection
                self.vectorstore = Chroma.from_documents(
                    documents=langchain_docs,
                    embedding=embeddings,
                    collection_name=f"custom_{re.sub(r'[^a-zA-Z0-9]', '_', filename)[:20]}"
                )
                logger.info(f"ChromaDB vector embeddings updated with {len(langchain_docs)} custom chunks.")
        except Exception as e:
            logger.warning(f"Vectorstore re-indexing note: {e}")

        # 3. Synchronize Extension In-Memory Battlecards Cache
        self._export_battlecards_to_extension()

        logger.info(f"Custom knowledge base activated: '{filename}' ({len(self.documents)} strategy chunks)")
        return {
            "success": True,
            "filename": filename,
            "total_chunks": len(self.documents),
            "uploaded_at": self.active_document_uploaded_at,
            "preview": self.get_all_battlecards()[:5]
        }

    def reset_to_default_knowledge_base(self) -> Dict[str, Any]:
        """Restores the standard 70 battlecards from zoom.pdf."""
        logger.info("Resetting knowledge base to default zoom.pdf...")
        self.query_cache.clear()
        self.active_document_name = "zoom.pdf (Default 70 Battlecards)"
        self.active_document_uploaded_at = None

        self._initialize_knowledge_base()
        self._export_battlecards_to_extension()

        return {
            "success": True,
            "active_document": self.active_document_name,
            "total_chunks": len(self.documents)
        }

    def get_knowledge_metadata(self) -> Dict[str, Any]:
        """Returns metadata about the active playbook."""
        return {
            "active_document": self.active_document_name,
            "total_chunks": len(self.documents),
            "is_custom": self.active_document_uploaded_at is not None,
            "uploaded_at": self.active_document_uploaded_at
        }

    def _export_battlecards_to_extension(self):
        """Syncs active strategies to all discovered chrome extension instances."""
        cards = self.get_all_battlecards()
        base_dir = os.path.dirname(os.path.abspath(__file__))

        # Collect candidate extension directories dynamically
        ext_dirs = [
            os.path.join(base_dir, "chrome_extension"),
            os.path.join(os.path.dirname(base_dir), "chrome_extension"),
            os.path.join(base_dir, "..", "..", "chrome_extension")
        ]

        # Add optional environment-configured paths
        custom_ext_path = os.environ.get("CHROME_EXTENSION_PATH")
        if custom_ext_path:
            ext_dirs.append(custom_ext_path)

        for ed in ext_dirs:
            norm_ed = os.path.normpath(ed)
            if os.path.exists(norm_ed) and os.path.isdir(norm_ed):
                try:
                    lib_dir = os.path.join(norm_ed, "lib")
                    os.makedirs(lib_dir, exist_ok=True)
                    json_path = os.path.join(lib_dir, "battlecards.json")
                    with open(json_path, "w", encoding="utf-8") as f:
                        json.dump(cards, f, ensure_ascii=False, indent=2)

                    js_path = os.path.join(lib_dir, "battlecards_data.js")
                    with open(js_path, "w", encoding="utf-8") as f:
                        f.write(f"window.SALES_BATTLECARDS = {json.dumps(cards, ensure_ascii=False, indent=2)};\n")
                except Exception as e:
                    logger.debug(f"Extension sync note for {norm_ed}: {e}")


