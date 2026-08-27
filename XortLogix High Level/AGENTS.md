# AGENTS.md — Workspace Guidelines & Rules

## Core Guidelines

1. **Strict Response Generation & Factual Accuracy Rules**:
   - Follow [.agents/rules/strict_proposal_rules.md](file:///.agents/rules/strict_proposal_rules.md).
   - Never invent candidate experience, metrics, client names, case studies, or portfolio items.
   - Separate Verified Experience, Client Requirements, and Proposed Recommendations.
   - Mark any unverified or missing information as `[CANDIDATE INPUT REQUIRED]`.

2. **Technical Standards**:
   - Use official, valid Google Gemini API models (`gemini-2.5-flash`, `gemini-2.0-flash`, `gemini-1.5-flash`).
   - Maintain codebase integrity for FastAPI backend (`app.py`), RAG engine (`rag_engine.py`), and frontend (`static/app.js`).
