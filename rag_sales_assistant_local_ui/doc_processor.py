# doc_processor.py
"""
Multi-Format Sales Document Ingestion & Intelligent Strategy Chunker.
Supports PDF, DOCX, TXT, Markdown, and CSV files.
Splits custom sales playbooks into structured Battlecard Chunks with rich semantic metadata.
"""

import os
import io
import re
import csv
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("DocProcessor")

def sanitize_unicode(text: str) -> str:
    """Removes lone unicode surrogates and unencodable characters that break JSON serialization."""
    if not isinstance(text, str):
        return ""
    # Strip lone surrogates
    cleaned = "".join(ch for ch in text if not (0xD800 <= ord(ch) <= 0xDFFF))
    return cleaned.encode("utf-8", "ignore").decode("utf-8", "ignore")

class DocumentProcessor:
    @staticmethod
    def extract_text(file_bytes: bytes, filename: str) -> str:
        """Extracts plain text from various file formats."""
        ext = os.path.splitext(filename)[1].lower()

        if ext == ".pdf":
            try:
                from pypdf import PdfReader
                reader = PdfReader(io.BytesIO(file_bytes))
                pages = [p.extract_text() or "" for p in reader.pages]
                raw_text = "\n".join(pages).strip()
                return sanitize_unicode(raw_text)
            except Exception as e:
                logger.error(f"Error parsing PDF {filename}: {e}")
                raise ValueError(f"Failed to read PDF document: {e}")

        elif ext in (".docx", ".doc"):
            try:
                import docx
                doc = docx.Document(io.BytesIO(file_bytes))
                full_text = []
                for para in doc.paragraphs:
                    if para.text.strip():
                        full_text.append(para.text.strip())
                for table in doc.tables:
                    for row in table.rows:
                        row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                        if row_text:
                            full_text.append(" | ".join(row_text))
                return sanitize_unicode("\n".join(full_text).strip())
            except Exception as e:
                # Fallback to XML extraction from zip
                try:
                    import zipfile
                    import xml.etree.ElementTree as ET
                    with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
                        xml_content = zf.read('word/document.xml')
                        tree = ET.fromstring(xml_content)
                        texts = [node.text for node in tree.iter() if node.text]
                        return sanitize_unicode(" ".join(texts).strip())
                except Exception as inner_e:
                    logger.error(f"Error parsing DOCX {filename}: {e} / {inner_e}")
                    raise ValueError(f"Failed to read Word document: {e}")

        elif ext in (".txt", ".md", ".json", ".log"):
            try:
                return sanitize_unicode(file_bytes.decode("utf-8", errors="ignore").strip())
            except Exception as e:
                logger.error(f"Error reading text file {filename}: {e}")
                raise ValueError(f"Failed to read text file: {e}")

        elif ext == ".csv":
            try:
                content = sanitize_unicode(file_bytes.decode("utf-8", errors="ignore"))
                reader = csv.reader(io.StringIO(content))
                rows = []
                for r in reader:
                    if any(r):
                        rows.append(" | ".join([c.strip() for c in r if c.strip()]))
                return "\n".join(rows).strip()
            except Exception as e:
                logger.error(f"Error reading CSV {filename}: {e}")
                raise ValueError(f"Failed to read CSV: {e}")

        else:
            # Attempt generic UTF-8 fallback
            try:
                return sanitize_unicode(file_bytes.decode("utf-8", errors="ignore").strip())
            except Exception:
                raise ValueError(f"Unsupported file format '{ext}'. Please upload PDF, DOCX, TXT, MD, or CSV.")

    @classmethod
    def chunk_strategies(cls, text: str, source_filename: str) -> List[Dict[str, Any]]:
        """
        Intelligently parses extracted text into structured strategy battlecards.
        Detects Q&A / Objection patterns, markdown sections, or semantic paragraphs.
        """
        if not text or len(text.strip()) < 10:
            return []

        # Normalize line indents and encoding artifacts
        clean_text = sanitize_unicode(text.replace("\ufffd", "-").replace("\u00ad", ""))
        raw_lines = [l.strip() for l in clean_text.splitlines()]
        clean_text = "\n".join([l for l in raw_lines if l])

        # 1. Check for Structured Q&A / Objection Blocks (e.g. Q1., Q:, Objection:, Scenario:)
        split_pattern = r'(?=(?:^|\n)\s*(?:Q\d+\.?|Q\s*:|Question\b|Objection\b|Scenario\b|Client\s+(?:says|asks|demands|requires)\b))'
        raw_blocks = [b.strip() for b in re.split(split_pattern, clean_text, flags=re.IGNORECASE) if b.strip()]

        structured_cards = []

        if len(raw_blocks) >= 2 or any(re.match(r'^(?:Q\d+\.?|Q\s*:|Question\b|Objection\b|Scenario\b|Client\s+(?:says|asks|demands|requires)\b)', b, re.IGNORECASE) for b in raw_blocks):
            card_id = 1
            for block in raw_blocks:
                if not re.match(r'^(?:Q\d+\.?|Q\s*:|Question\b|Objection\b|Scenario\b|Client\s+(?:says|asks|demands|requires)\b)', block, re.IGNORECASE):
                    continue

                # Pattern A: Standard format with Context & Pitch
                sub_m = re.search(r'^(?:Q\d+\.?|Q\s*:|Question(?:\s*\d+)?:?|Objection(?:\s*\d+)?:?|Scenario(?:\s*\d+)?:?|Client\s+(?:says|asks|demands|requires):?)\s*(.+?)\n+(?:Context\s*/\s*Rationale|Context|Background|Why)\s*\n+(.+?)\n+(?:Exact\s*Strategy\s*/\s*Pitch|Pitch|Strategy|Response|Answer|Solution)\s*\n+(.+)', block, re.DOTALL | re.IGNORECASE)
                if sub_m:
                    q_text = sub_m.group(1).strip()
                    context_text = sub_m.group(2).strip()
                    pitch_text = sub_m.group(3).strip()
                else:
                    # Pattern B: Question -> Answer / Pitch / Strategy
                    sub_m2 = re.search(r'^(?:Q\d+\.?|Question(?:\s*\d+)?:?|Objection(?:\s*\d+)?:?|Scenario(?:\s*\d+)?:?|Client(?:\s*says)?:?)\s*(.+?)\n+(?:Answer:?|Pitch:?|Response:?|Strategy:?|Solution:?)\s*\n+(.+)', block, re.DOTALL | re.IGNORECASE)
                    if sub_m2:
                        q_text = sub_m2.group(1).strip()
                        pitch_text = sub_m2.group(2).strip()
                        context_text = f"Custom strategy for objection: {q_text[:80]}"
                    else:
                        # Pattern C: First line is question, rest is pitch
                        lines = [line.strip() for line in block.split("\n") if line.strip()]
                        if len(lines) >= 2:
                            q_text = re.sub(r'^(?:Q\d+\.?|Question(?:\s*\d+)?:?|Objection(?:\s*\d+)?:?|Scenario(?:\s*\d+)?:?|Client(?:\s*says)?:?)\s*', '', lines[0], flags=re.IGNORECASE).strip()
                            pitch_text = "\n".join(lines[1:]).strip()
                            context_text = f"Sales strategy playbook entry from {source_filename}"
                        else:
                            continue

                if q_text and pitch_text:
                    structured_cards.append({
                        "q_number": card_id,
                        "question": sanitize_unicode(q_text),
                        "context": sanitize_unicode(context_text),
                        "pitch": sanitize_unicode(pitch_text),
                        "source": sanitize_unicode(source_filename)
                    })
                    card_id += 1

        # 2. Check for Markdown Headers (e.g. ## Objection / Strategy)
        if len(structured_cards) < 2:
            header_blocks = re.split(r'(?:^|\n)(?=#{1,4}\s+)', clean_text)
            card_id = 1
            for hb in header_blocks:
                hb = hb.strip()
                if not hb or len(hb) < 20:
                    continue
                lines = [l.strip() for l in hb.split("\n") if l.strip()]
                if len(lines) >= 2:
                    header = re.sub(r'^#{1,4}\s*', '', lines[0]).strip()
                    body = "\n".join(lines[1:]).strip()
                    structured_cards.append({
                        "q_number": card_id,
                        "question": sanitize_unicode(header),
                        "context": f"Section: {header} from {source_filename}",
                        "pitch": sanitize_unicode(body),
                        "source": sanitize_unicode(source_filename)
                    })
                    card_id += 1

        # 3. Fallback: Semantic Paragraph Chunker (150-250 words per chunk)
        if len(structured_cards) < 1:
            paragraphs = [p.strip() for p in re.split(r'\n\s*\n', clean_text) if len(p.strip()) > 30]
            card_id = 1
            for p in paragraphs:
                first_sentence_m = re.match(r'^([^.!?\n]+[.!?])', p)
                first_sentence = first_sentence_m.group(1).strip() if first_sentence_m else p[:60] + "..."
                structured_cards.append({
                    "q_number": card_id,
                    "question": sanitize_unicode(f"Topic: {first_sentence}"),
                    "context": sanitize_unicode(f"Document context from {source_filename}"),
                    "pitch": sanitize_unicode(p),
                    "source": sanitize_unicode(source_filename)
                })
                card_id += 1

        logger.info(f"Chunked '{source_filename}' into {len(structured_cards)} strategy battlecards.")
        return structured_cards
