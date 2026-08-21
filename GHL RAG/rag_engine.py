import os
import re
import gc
import json
import time
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

# ==========================================
# 1. DATA STRUCTURES
# ==========================================

@dataclass
class QueryAnalysis:
    raw_query: str
    cleaned_query: str
    intent: str
    objective: str
    core_entities: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    output_type: str = "general_explanation"
    expanded_queries: List[str] = field(default_factory=list)
    is_conversational: bool = False
    is_complex: bool = False
    is_out_of_scope: bool = False

@dataclass
class RetrievedChunk:
    chunk_id: str
    content: str
    score: float = 0.0
    source: str = "ghl_knowledge_base"
    match_type: str = "vector"
    metadata: Dict[str, Any] = field(default_factory=dict)


# ==========================================
# 2. QUERY UNDERSTANDING & INTENT ENGINE
# ==========================================

class QueryUnderstandingEngine:
    """
    Analyzes user query to determine:
    1. Intent (job_posting_analysis, technical_troubleshooting, system_architecture,
       business_strategy, comparison_evaluation, factual_lookup, conversational, out_of_scope)
    2. Core Entities & Concepts
    3. Output Type & Formatting Goals
    4. Adaptive Query Expansion (sub-queries for complex inputs)
    """

    GREETING_PATTERNS = {
        "hi", "hello", "hey", "hey there", "hello there", "greetings",
        "good morning", "good afternoon", "good evening", "good day",
        "aoa", "assalam o alaikum", "assalam-o-alaikum", "assalamu alaikum",
        "salam", "slaam", "wsalam", "how are you", "how are you?",
        "how r u", "who are you", "who are you?", "what can you do",
        "what can you do?", "help", "help me", "hi bot", "hello bot"
    }

    INTENT_OPENER_PATTERNS = {
        "i want to learn one thing", "i want to learn something", "i want to learn",
        "i want to learn ghl", "i have a question", "can i ask a question",
        "can i ask something", "i want to ask something", "can you help me",
        "i need help", "help me", "can you teach me", "teach me",
        "tell me about yourself", "how does this work", "help me with ghl",
        "i need some help", "i need assistance"
    }

    OUT_OF_SCOPE_KEYWORDS = {
        "recipe", "cooking", "how to bake", "cake", "chocolate", "pizza",
        "weather in", "forecast", "cricket score", "football match", "fifa",
        "hollywood", "bollywood", "celebrity", "movie review", "horoscope",
        "astrology", "gaming tips", "playstation", "minecraft", "gta 5"
    }

    @classmethod
    def analyze(cls, query: str, user_name: str = "User", history: List[Dict[str, Any]] = None) -> QueryAnalysis:
        raw_text = query.strip()
        cleaned_text = raw_text.lower().rstrip('.!?')
        words = cleaned_text.split()
        word_count = len(words)

        # 1. Check for Conversational Openers & Greetings
        if cleaned_text in cls.GREETING_PATTERNS or (
            any(cleaned_text.startswith(p) for p in ["i want to learn", "can you teach me", "i want to ask", "can i ask", "i have a question"])
            and word_count <= 7
        ) or cleaned_text in cls.INTENT_OPENER_PATTERNS:
            return QueryAnalysis(
                raw_query=raw_text,
                cleaned_query=cleaned_text,
                intent="conversational_greeting",
                objective="Acknowledge user warmly and offer GHL assistance.",
                core_entities=["GoHighLevel"],
                topics=["Introduction", "Assistance"],
                output_type="conversational_reply",
                expanded_queries=[],
                is_conversational=True,
                is_complex=False
            )

        # 2. Check for Strict Out-of-Scope Topics (Non-GHL)
        if any(kw in cleaned_text for kw in cls.OUT_OF_SCOPE_KEYWORDS):
            # Verify if GHL is explicitly mentioned
            if not any(ghl_term in cleaned_text for ghl_term in ["ghl", "gohighlevel", "crm", "workflow", "funnel", "pipeline"]):
                return QueryAnalysis(
                    raw_query=raw_text,
                    cleaned_query=cleaned_text,
                    intent="out_of_scope",
                    objective="Politely decline out-of-scope question and state GHL domain expertise.",
                    core_entities=[],
                    topics=["Off-Topic"],
                    output_type="out_of_scope_notice",
                    expanded_queries=[],
                    is_conversational=False,
                    is_complex=False,
                    is_out_of_scope=True
                )

        # 3. Detect Job Postings, RFPs, Client/Agent Acquisition & Hiring Requirements
        job_signals = [
            "growth & campaign specialist", "campaign specialist", "specialist",
            "we are looking for", "responsibilities", "what you will be responsible for",
            "primary objectives", "compensation", "how to apply", "first 90-day",
            "ideal candidate", "bonus skills", "not a good fit", "results we expect",
            "client acquisition", "agent acquisition", "hiring", "job description",
            "job offer", "financial freedom roadmap", "financial freedom fast track",
            "licensed financial", "tdt financial"
        ]
        job_matches = sum(1 for signal in job_signals if signal in cleaned_text)
        is_job_posting = job_matches >= 2 or (
            any(s in cleaned_text for s in ["growth & campaign specialist", "job description", "we are looking for"]) 
            and word_count > 40
        )

        if is_job_posting:
            entities = cls._extract_entities(raw_text)
            expanded = cls._generate_job_expanded_queries(cleaned_text, entities)
            return QueryAnalysis(
                raw_query=raw_text,
                cleaned_query=cleaned_text,
                intent="job_posting_analysis",
                objective="Analyze company needs, required technical/marketing skills, expected KPIs, candidate evaluation criteria, and formulate a winning application strategy.",
                core_entities=entities,
                topics=["Campaign Strategy", "Funnel Building", "Lead Generation", "Automations", "Client Acquisition", "Recruiting Funnel"],
                output_type="job_analysis_and_strategy",
                expanded_queries=expanded,
                is_conversational=False,
                is_complex=True
            )

        # 4. Detect Technical Troubleshooting & Error Debugging
        troubleshoot_signals = [
            "error", "failed", "not working", "issue", "bug", "500", "404", "403",
            "troubleshoot", "why is my", "webhook failing", "trigger not firing",
            "contact not added", "email not sending", "sms failed", "broken", "fix"
        ]
        is_troubleshooting = any(sig in cleaned_text for sig in troubleshoot_signals) and (
            "workflow" in cleaned_text or "ghl" in cleaned_text or "trigger" in cleaned_text or
            "webhook" in cleaned_text or "pipeline" in cleaned_text or "integration" in cleaned_text or word_count > 15
        )

        if is_troubleshooting:
            entities = cls._extract_entities(raw_text)
            expanded = [
                f"{e} troubleshooting configuration fix" for e in entities[:2]
            ] or ["workflow trigger error troubleshooting", "webhook integration setup"]
            return QueryAnalysis(
                raw_query=raw_text,
                cleaned_query=cleaned_text,
                intent="technical_troubleshooting",
                objective="Identify root cause, probable failure points, and provide verified step-by-step resolution in GoHighLevel.",
                core_entities=entities,
                topics=["Troubleshooting", "Error Resolution", "Workflows", "Triggers"],
                output_type="troubleshooting_guide",
                expanded_queries=expanded[:3],
                is_conversational=False,
                is_complex=True
            )

        # 5. Detect System / Workflow Architecture & Multi-Step Funnel Setup
        architecture_signals = [
            "how to build", "how to setup", "how to create a workflow", "how to integrate",
            "step by step", "architecture", "pipeline setup", "multi-step",
            "client onboarding", "booking funnel", "appointment system", "automation system"
        ]
        is_architecture = any(sig in cleaned_text for sig in architecture_signals) or (
            word_count > 30 and ("workflow" in cleaned_text or "funnel" in cleaned_text or "automation" in cleaned_text)
        )

        if is_architecture:
            entities = cls._extract_entities(raw_text)
            expanded = [
                f"{e} workflow automation setup" for e in entities[:2]
            ] + ["GoHighLevel workflow triggers and actions", "pipeline stage automations"]
            return QueryAnalysis(
                raw_query=raw_text,
                cleaned_query=cleaned_text,
                intent="system_architecture",
                objective="Provide an executive, end-to-end technical blueprint with triggers, actions, custom values, and pipeline automations.",
                core_entities=entities,
                topics=["System Architecture", "Workflow Automation", "Funnels", "Pipelines"],
                output_type="architecture_blueprint",
                expanded_queries=expanded[:3],
                is_conversational=False,
                is_complex=True
            )

        # 6. Detect Business Strategy & Lead Generation Planning
        strategy_signals = [
            "strategy", "marketing plan", "lead generation", "conversion optimization",
            "increase show rate", "scale", "acquisition system", "campaign ideas"
        ]
        is_strategy = any(sig in cleaned_text for sig in strategy_signals)

        if is_strategy:
            entities = cls._extract_entities(raw_text)
            expanded = [
                "GoHighLevel lead generation campaigns funnels",
                "automated appointment follow-up workflows",
                "campaign tracking metrics reporting"
            ]
            return QueryAnalysis(
                raw_query=raw_text,
                cleaned_query=cleaned_text,
                intent="business_strategy",
                objective="Outline a scalable growth strategy, campaign funnels, and KPI metrics.",
                core_entities=entities,
                topics=["Business Strategy", "Lead Gen", "Conversion Rate", "Campaigns"],
                output_type="strategic_plan",
                expanded_queries=expanded,
                is_conversational=False,
                is_complex=True
            )

        # 7. Detect Comparison / Evaluation
        if any(k in cleaned_text for k in ["difference between", " vs ", "versus", "compare", "which is better"]):
            entities = cls._extract_entities(raw_text)
            return QueryAnalysis(
                raw_query=raw_text,
                cleaned_query=cleaned_text,
                intent="comparison_evaluation",
                objective="Compare and contrast features, benefits, use cases, and limitations.",
                core_entities=entities,
                topics=["Comparison", "Evaluation"],
                output_type="comparative_breakdown",
                expanded_queries=[f"{e} overview features" for e in entities[:2]],
                is_conversational=False,
                is_complex=False
            )

        # 8. Default: Factual Lookup or General Technical Query
        is_complex = word_count > 30
        entities = cls._extract_entities(raw_text)
        expanded = [cleaned_text[:120]] if not is_complex else [
            cleaned_text[:120],
            f"{entities[0]} GoHighLevel feature setup" if entities else "GoHighLevel features"
        ]

        return QueryAnalysis(
            raw_query=raw_text,
            cleaned_query=cleaned_text,
            intent="factual_lookup" if not is_complex else "general_technical",
            objective="Provide accurate technical explanation based on official GoHighLevel documentation.",
            core_entities=entities,
            topics=["Technical Support"],
            output_type="direct_concise" if not is_complex else "detailed_technical",
            expanded_queries=expanded[:2],
            is_conversational=False,
            is_complex=is_complex
        )

    @classmethod
    def _extract_entities(cls, text: str) -> List[str]:
        entities = []
        known_keywords = [
            "Workflow", "Workflows", "Trigger", "Triggers", "Action", "Actions",
            "Custom Values", "Custom Fields", "Funnel", "Funnels", "Landing Page",
            "Form", "Forms", "Survey", "Surveys", "Calendar", "Calendars",
            "Pipeline", "Pipelines", "Opportunity", "Opportunities", "Webhook", "Webhooks",
            "REST API", "API", "Sub-account", "Sub-accounts", "Snapshot", "Snapshots",
            "Email Automation", "SMS Automation", "Lead Magnet", "Appointment Booking",
            "Conversion Rate", "A/B Testing", "Affiliate Manager", "Memberships",
            "SaaS Mode", "LC Phone", "LC Email", "Mailgun", "Twilio", "Stripe"
        ]
        text_lower = text.lower()
        for kw in known_keywords:
            if kw.lower() in text_lower and kw not in entities:
                entities.append(kw)
        return entities[:6]

    @classmethod
    def _generate_job_expanded_queries(cls, text: str, entities: List[str]) -> List[str]:
        queries = [
            "GoHighLevel marketing campaigns lead generation funnels",
            "automated SMS email nurturing workflows appointment booking",
            "client acquisition agent recruiting pipeline setup",
            "campaign tracking reporting metrics conversion rate"
        ]
        return queries


# ==========================================
# 3. HYBRID RETRIEVAL & RERANKING
# ==========================================

class HybridRetriever:
    """
    Executes hybrid search (Semantic Vector via FastEmbed ONNX + Keyword token matching)
    and combines results across original query and expanded sub-queries using Reciprocal Rank Fusion (RRF).
    """

    @classmethod
    def search(cls, analysis: QueryAnalysis, chroma_col, embed_model, top_k: int = 5) -> List[RetrievedChunk]:
        if not chroma_col:
            return []

        search_queries = []
        # Primary query (truncated to 300 chars for safe embedding)
        search_queries.append(analysis.raw_query[:300].strip())

        # Add expanded queries if complex
        if analysis.is_complex and analysis.expanded_queries:
            search_queries.extend(analysis.expanded_queries[:3])

        all_candidates: Dict[str, Dict[str, Any]] = {}
        rrf_k = 60

        # Single-pass batch embedding for ultra-low memory & fast execution
        batch_inputs = [f"search_query: {q}" for q in search_queries if q]
        query_embs = []
        if embed_model and batch_inputs:
            try:
                if hasattr(embed_model, 'embed'):
                    embs = list(embed_model.embed(batch_inputs))
                    query_embs = [e.tolist() if hasattr(e, 'tolist') else list(e) for e in embs]
                elif hasattr(embed_model, 'encode'):
                    query_embs = embed_model.encode(batch_inputs).tolist()
            except Exception as e_emb:
                print(f"⚠️ Batch embedding note: {e_emb}")

        # Execute vector queries
        for q_idx, query_emb in enumerate(query_embs):
            try:
                res = chroma_col.query(query_embeddings=[query_emb], n_results=min(top_k * 2, 6))
                if res and res.get('documents') and len(res['documents']) > 0:
                    docs = res['documents'][0]
                    metas = res['metadatas'][0] if res.get('metadatas') else [{}] * len(docs)
                    ids = res['ids'][0] if res.get('ids') else [hashlib.md5(d.encode('utf-8')).hexdigest() for d in docs]
                    distances = res['distances'][0] if res.get('distances') else [0.5] * len(docs)

                    for rank, (doc_id, doc_text, meta, dist) in enumerate(zip(ids, docs, metas, distances)):
                        if not doc_text or len(doc_text.strip()) < 20:
                            continue
                        if doc_id not in all_candidates:
                            all_candidates[doc_id] = {
                                'id': doc_id,
                                'content': doc_text,
                                'meta': meta or {},
                                'vector_score': 1.0 / (1.0 + float(dist)),
                                'rrf_score': 0.0,
                                'keyword_score': 0.0,
                                'query_hits': 0
                            }
                        all_candidates[doc_id]['rrf_score'] += 1.0 / (rrf_k + rank + 1)
                        all_candidates[doc_id]['query_hits'] += 1
            except Exception as e_q:
                print(f"⚠️ Vector search query note: {e_q}")

        # B. Keyword / Exact Token Match Retrieval
        keyword_targets = analysis.core_entities[:3]
        for kw in keyword_targets:
            if len(kw) < 3:
                continue
            try:
                kw_res = chroma_col.get(where_document={"$contains": kw}, limit=3)
                if kw_res and kw_res.get('documents'):
                    kw_docs = kw_res['documents']
                    kw_ids = kw_res.get('ids', [hashlib.md5(d.encode('utf-8')).hexdigest() for d in kw_docs])
                    kw_metas = kw_res.get('metadatas', [{}] * len(kw_docs))
                    for rank, (doc_id, doc_text, meta) in enumerate(zip(kw_ids, kw_docs, kw_metas)):
                        if doc_id not in all_candidates:
                            all_candidates[doc_id] = {
                                'id': doc_id,
                                'content': doc_text,
                                'meta': meta or {},
                                'vector_score': 0.5,
                                'rrf_score': 0.0,
                                'keyword_score': 0.0,
                                'query_hits': 0
                            }
                        all_candidates[doc_id]['keyword_score'] += 0.3
                        all_candidates[doc_id]['rrf_score'] += 1.0 / (rrf_k + rank + 1)
            except Exception as e_kw:
                pass

        # Clean memory immediately after vector operations
        gc.collect()

        if not all_candidates:
            return []

        # C. Rerank & Score Candidates
        ranked_chunks: List[RetrievedChunk] = []
        for cand in all_candidates.values():
            # Composite relevance score
            composite_score = (cand['rrf_score'] * 2.0) + (cand['vector_score'] * 0.5) + (cand['keyword_score'] * 0.3)
            
            # Boost score if chunk contains multiple core entities
            content_lower = cand['content'].lower()
            entity_matches = sum(1 for e in analysis.core_entities if e.lower() in content_lower)
            composite_score += (entity_matches * 0.1)

            ranked_chunks.append(RetrievedChunk(
                chunk_id=cand['id'],
                content=cand['content'],
                score=round(composite_score, 4),
                source=cand['meta'].get('source', 'GoHighLevel Official Documentation'),
                metadata=cand['meta']
            ))

        # Sort descending by composite score
        ranked_chunks.sort(key=lambda x: x.score, reverse=True)

        # Deduplicate and return top_k
        seen_hashes = set()
        deduped: List[RetrievedChunk] = []
        for c in ranked_chunks:
            # Hash first 150 chars to avoid semantic duplicate paragraphs
            c_hash = hashlib.md5(c.content[:150].strip().lower().encode('utf-8')).hexdigest()
            if c_hash not in seen_hashes:
                seen_hashes.add(c_hash)
                deduped.append(c)
                if len(deduped) >= top_k:
                    break

        return deduped


# ==========================================
# 4. CONTEXT ASSEMBLER
# ==========================================

class ContextAssembler:
    """
    Builds clean, logically ordered, deduplicated context within model token boundaries.
    Also incorporates user profile and conversation history for conversational continuity.
    """

    @classmethod
    def assemble(
        cls,
        analysis: QueryAnalysis,
        chunks: List[RetrievedChunk],
        user_name: str = "User",
        history: List[Dict[str, Any]] = None
    ) -> Tuple[str, List[str]]:
        if not chunks:
            return "Standard GoHighLevel Knowledge Base (No specific chunk matches).", []

        context_blocks = []
        source_labels = []

        for idx, chunk in enumerate(chunks, 1):
            src = chunk.metadata.get('title') or chunk.source or f"Documentation Section {idx}"
            source_labels.append(src)
            context_blocks.append(f"--- DOCUMENT EXCERPT {idx} [{src}] ---\n{chunk.content.strip()}")

        assembled_str = "\n\n".join(context_blocks)
        return assembled_str, list(dict.fromkeys(source_labels))


# ==========================================
# 5. INTENT-AWARE PROMPT BUILDER
# ==========================================

class IntentAwarePromptBuilder:
    """
    Constructs high-intelligence, domain-independent system prompts customized for the detected user intent.
    Ensures the LLM acts as an expert consultant rather than a simple document regurgitator.
    """

    @classmethod
    def build_prompt(
        cls,
        analysis: QueryAnalysis,
        context_str: str,
        user_name: str = "there",
        is_first_message: bool = True,
        history_summary: str = ""
    ) -> str:
        first_name = user_name.split()[0].capitalize() if user_name else "there"

        # Base Persona & Consultant Standard
        base_header = f"""You are an elite GoHighLevel (GHL) Senior Technical Consultant & AI Growth Architect.
User's Name: {first_name}
Is Opening Conversation: {is_first_message}
User Detected Intent: {analysis.intent}
Primary Objective: {analysis.objective}
"""

        # Tailored Intent Instructions
        if analysis.intent == "job_posting_analysis":
            intent_guidance = """
MISSION & ADAPTIVE STRUCTURE FOR JOB DESCRIPTION / RFP ANALYSIS:
The user provided a detailed Job Posting / Growth Specialist Opportunity.
Do NOT merely summarize or parrot the job description back to the user.
Act as an elite Marketing & GoHighLevel Architect who deeply understands what makes a growth system succeed.

Provide a comprehensive, executive-level breakdown using the following structured sections:

### 1. 🎯 What the Company Actually Needs
- Analyze the core business objective and underlying challenge (e.g. scaling client acquisition, agent recruitment funnels, end-to-end automation).
- Differentiate between the client acquisition track and the agent recruitment track.

### 2. ⚡ Core Technical & GoHighLevel Requirements
- Outline the exact GHL architecture required (Funnels, SMS/Email 2-way nurturing, Appointment Calendars, Pipelines, Custom Values, Tags, and Campaign Triggers).
- Mention required integrations (Meta/Google Ads, Zapier, Webhooks, LC Phone/Email).

### 3. 📊 Expected Deliverables & Measurable KPIs
- Detail how success will be measured (Cost Per Lead, Show-Up Rate, Cost Per Acquisition, Booking Conversion Rate, Campaign ROI).

### 4. 🔍 Key Evaluation Criteria & Information Gaps
- What a top-tier candidate must demonstrate to stand out (proven results, system duplication, conversion tracking).
- Identify missing details or variables in the job post (e.g. current ad spend, sub-account setup, existing CRM database size).

### 5. 🏗️ Recommended Implementation Blueprint
- Provide the step-by-step GoHighLevel acquisition system architecture:
  * Ad/Lead Magnet → Landing Page / Survey Form → Pipeline Stage → Instant SMS/Email Follow-up → Calendar Booking → Automated Show-up Reminders → Closed Client/Agent.

### 6. 💼 High-Impact Pitch & Application Strategy
- Provide an authoritative, battle-tested pitch / application letter tailored specifically to this role that the user can use or adapt.
- Focus on measurable outcomes, conversion optimization, and GHL system ownership.
- (Note: Do NOT invent unprovided personal credentials or fake metrics; formulate it based on professional GHL execution standards).
"""

        elif analysis.intent == "technical_troubleshooting":
            intent_guidance = """
MISSION & ADAPTIVE STRUCTURE FOR TECHNICAL TROUBLESHOOTING:
The user is experiencing a technical issue, bug, or configuration challenge.
Diagnose and resolve the issue systematically:

### 1. 🔍 Problem Diagnosis & Likely Root Causes
- Pinpoint the exact failure points in GoHighLevel (e.g. workflow trigger conditions, custom field mapping, unassigned user, webhook payload format, SMS/Email deliverability settings).

### 2. 🛠️ Step-by-Step Resolution
- Provide precise, step-by-step instructions inside GoHighLevel to fix the issue.
- Include exact navigation paths (e.g., Automation → Workflows → Settings → Action Execution).

### 3. 🟡 Workarounds & Third-Party Fallbacks (If Applicable)
- If native GHL feature has limitations, provide the recommended webhook, custom code, or Zapier/Make workaround.

### 4. ✅ Verification & Testing Steps
- How to test and verify the fix using GHL execution logs or contact test mode.
"""

        elif analysis.intent == "system_architecture":
            intent_guidance = """
MISSION & ADAPTIVE STRUCTURE FOR SYSTEM / WORKFLOW ARCHITECTURE:
The user wants to build a multi-step automation, funnel, or system.
Provide an executive, ready-to-implement technical blueprint:

### 1. 🏗️ System Architecture Overview
- Flowchart logic and trigger/action sequence.

### 2. ⚡ Step-by-Step GoHighLevel Configuration
- Triggers: Exact trigger filters and conditions.
- Actions: Sequential workflow actions (Tagging, Custom Fields, Wait Steps, Webhooks, Notifications).
- Pipelines: Opportunity stages and stage change automations.

### 3. 🛡️ Failsafes & Edge-Case Handling
- Handling no-shows, unread SMS, re-engagement workflows, and stop-on-response rules.
"""

        elif analysis.intent == "business_strategy":
            intent_guidance = """
MISSION & ADAPTIVE STRUCTURE FOR GROWTH STRATEGY:
The user is asking for growth strategy, lead gen systems, or conversion improvement.
Provide actionable, high-ROI marketing & automation strategy:
- Strategic acquisition channels (Paid Ads, Lead Magnets, VSL/Webinar funnels).
- Conversion rate optimization (Landing pages, surveys, booking rate, show-up rate).
- Automated nurture sequences (SMS + Email + Voicemail drops).
- Key performance indicators (KPIs) and dashboard tracking.
"""

        elif analysis.intent == "comparison_evaluation":
            intent_guidance = """
MISSION & ADAPTIVE STRUCTURE FOR FEATURE / TOOL COMPARISON:
- Feature-by-feature comparative breakdown.
- Key strengths, weaknesses, and ideal use cases.
- Concrete recommendation based on scale, cost, and technical capability.
"""

        elif analysis.intent == "factual_lookup":
            intent_guidance = """
MISSION FOR DIRECT FACTUAL QUERY:
- Deliver a direct, crisp, and concise answer immediately.
- Do NOT generate long unnecessary sections or boilerplate.
- Keep simple questions short, direct, and actionable.
"""

        else:
            intent_guidance = """
MISSION FOR GENERAL TECHNICAL QUERY:
- Start with an executive status banner on the very first line:
  - Native feature: "### 🟢 Native GoHighLevel Feature"
  - Workaround required: "### 🟡 Workaround / Third-Party Integration Required"
  - General technical overview: "### ℹ️ GoHighLevel Technical Overview"
- Provide a clear, direct, and actionable answer synthesized from the documentation context.
- Keep the response clean and structured.
"""

        # Universal Production Rules & Expert Guidelines
        rules = """
CORE CONSULTING & EXPERT PRINCIPLES:
1. COMPREHENSIVE EXPERTISE & ASSISTANCE:
   - You are the ultimate GoHighLevel Solutions Architect & Technical Consultant. Always provide helpful, in-depth, and practical explanations.
   - When the user asks general or foundational questions (e.g. "what is GHL", "how does GHL work", "explain pipelines"), give a clear, well-structured, professional breakdown covering GoHighLevel's core CRM, automation workflows, funnels, calendars, and SaaS capabilities.
   - When the user provides an attached document, image, PDF, or voice recording (e.g. a Zoom guide, marketing plan, workflow screenshot), thoroughly analyze the attachment and explain in detail how it integrates with or relates to GoHighLevel (e.g. connecting Zoom to GHL calendars, syncing contacts, triggering workflows, embedding meeting links, or setting up API/Webhook connections).

2. KNOWLEDGE BASE & SYNTHESIS:
   - Combine the retrieved Knowledge Base context with your extensive native GoHighLevel expertise (Workflows, Funnels, Triggers, Custom Values, Calendars, Pipelines, REST API v2, Webhooks, Marketplace apps, LC Phone/Email).
   - If a specific niche detail is not in the local knowledge base, provide the standard GoHighLevel best practices, workflow patterns, or recommended third-party workarounds (e.g. Zapier, Make, custom webhooks).
   - NEVER give a generic refusal or say information is not available if you can provide accurate architectural, workflow, or integration guidance.

3. GREETINGS & TONE:
   - If this is the FIRST message of a conversation, greet politely by name ({first_name}).
   - If this is an ONGOING conversation, DO NOT repeat "Hello [Name]" or "Hi [Name]". Answer directly, crisply, and professionally.
   - Maintain an authoritative, polished, and structured format using markdown headers, bullet points, and actionable steps.
4. NO RAW CHUNK DUMPING:
   - Do NOT append raw document chunks or citations dumps in the generated text. Present synthesized, cohesive insights.
"""

        full_prompt = f"""{base_header}
{intent_guidance}

{rules}

==================================================
KNOWLEDGE BASE CONTEXT:
==================================================
{context_str}

==================================================
USER QUERY:
==================================================
{analysis.raw_query}

ANSWER:"""

        return full_prompt


# ==========================================
# 6. MASTER RAG ENGINE ORCHESTRATOR
# ==========================================

class RAGEngine:
    """
    Main entrypoint coordinating:
    Query Analysis → Intent Detection → Hybrid Retrieval → Relevance Reranking → Prompt Synthesis
    """

    @classmethod
    def process_query(
        cls,
        user_query: str,
        chroma_col,
        embed_model,
        user_name: str = "there",
        is_first_message: bool = True,
        top_k: int = 5,
        history: List[Dict[str, Any]] = None
    ) -> Tuple[QueryAnalysis, str, List[str]]:
        start_t = time.time()

        # 1. Query Understanding & Intent Analysis
        analysis = QueryUnderstandingEngine.analyze(user_query, user_name=user_name, history=history)
        print(f"🧠 [RAG Engine] Detected Intent: {analysis.intent} | Output Type: {analysis.output_type} | Complex: {analysis.is_complex}")
        if analysis.expanded_queries:
            print(f"🔍 [RAG Engine] Expanded Queries ({len(analysis.expanded_queries)}): {analysis.expanded_queries}")

        # 2. Conversational Fast-Path
        if analysis.is_conversational:
            return analysis, "", []

        # 3. Hybrid Retrieval & Reranking
        retrieved_chunks = HybridRetriever.search(
            analysis=analysis,
            chroma_col=chroma_col,
            embed_model=embed_model,
            top_k=top_k
        )
        print(f"📦 [RAG Engine] Retrieved Chunks: {len(retrieved_chunks)} | Retrieval Latency: {round((time.time() - start_t)*1000, 1)}ms")

        # 4. Context Assembly
        context_str, source_labels = ContextAssembler.assemble(
            analysis=analysis,
            chunks=retrieved_chunks,
            user_name=user_name,
            history=history
        )

        # 5. Intent-Aware Prompt Construction
        prompt = IntentAwarePromptBuilder.build_prompt(
            analysis=analysis,
            context_str=context_str,
            user_name=user_name,
            is_first_message=is_first_message
        )

        return analysis, prompt, source_labels
