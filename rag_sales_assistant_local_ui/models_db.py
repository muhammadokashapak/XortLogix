# models_db.py
"""
Multi-Tenant SQLite Database Layer for Sales Co-Pilot AI.
Handles User Accounts, Role-Based Access Control (Admin/User),
Document Registry, Google Drive metadata, and Custom Chunk Persistence.
"""

import os
import sqlite3
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger("ModelsDB")

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sales_app.db")

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes multi-tenant database tables and seeds default Admin."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user',  -- 'admin' or 'user'
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL
    );
    """)

    # 2. Uploaded Documents Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        user_email TEXT NOT NULL,
        filename TEXT NOT NULL,
        file_size INTEGER NOT NULL,
        drive_file_id TEXT,
        drive_web_view_link TEXT,
        drive_folder_id TEXT,
        chunks_count INTEGER NOT NULL DEFAULT 0,
        uploaded_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """)

    # 3. Document Chunks Table (User Custom Strategy Chunks)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS document_chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doc_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        user_email TEXT NOT NULL,
        chunk_index INTEGER NOT NULL,
        title TEXT NOT NULL,
        text_content TEXT NOT NULL,
        strategy_pitch TEXT NOT NULL,
        context TEXT,
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (doc_id) REFERENCES documents (id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """)

    conn.commit()

    # 4. Auto-Seed Default Admin Account
    # Email: okashaxortlogix@gmail.com, Pass: adminokasha, Role: admin
    cursor.execute("SELECT id FROM users WHERE email = ?", ("okashaxortlogix@gmail.com",))
    admin_exists = cursor.fetchone()

    if not admin_exists:
        import bcrypt
        hashed = bcrypt.hashpw("adminokasha".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        now_str = datetime.utcnow().isoformat()
        cursor.execute("""
        INSERT INTO users (email, password_hash, full_name, role, is_active, created_at)
        VALUES (?, ?, ?, ?, 1, ?)
        """, ("okashaxortlogix@gmail.com", hashed, "Muhammad Okasha (Admin)", "admin", now_str))
        conn.commit()
        logger.info("👑 Default Admin account auto-seeded: okashaxortlogix@gmail.com (Role: admin)")

    conn.close()

# --- User Operations ---
def create_user(email: str, password_hash: str, full_name: str, role: str = "user") -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.utcnow().isoformat()
    try:
        cursor.execute("""
        INSERT INTO users (email, password_hash, full_name, role, is_active, created_at)
        VALUES (?, ?, ?, ?, 1, ?)
        """, (email.lower().strip(), password_hash, full_name.strip(), role, now_str))
        conn.commit()
        user_id = cursor.lastrowid
        return {
            "id": user_id,
            "email": email.lower().strip(),
            "full_name": full_name.strip(),
            "role": role,
            "is_active": 1,
            "created_at": now_str
        }
    finally:
        conn.close()

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def list_all_users() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, email, full_name, role, is_active, created_at FROM users ORDER BY id ASC")
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

def delete_user_by_id(user_id: int) -> bool:
    """Deletes a user and their associated documents & chunks. Protects primary admin."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT email, role FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            return False
        if user["email"] == "okashaxortlogix@gmail.com":
            raise ValueError("Primary Master Admin account cannot be deleted.")
        
        cursor.execute("DELETE FROM document_chunks WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM documents WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        logger.info(f"🗑️ Deleted user #{user_id} ({user['email']}) and all associated strategy chunks.")
        return True
    finally:
        conn.close()

# --- Document Operations ---
def create_document_record(
    user_id: int,
    user_email: str,
    filename: str,
    file_size: int,
    drive_file_id: Optional[str] = None,
    drive_web_view_link: Optional[str] = None,
    drive_folder_id: Optional[str] = None,
    chunks_count: int = 0
) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.utcnow().isoformat()
    try:
        cursor.execute("""
        INSERT INTO documents (user_id, user_email, filename, file_size, drive_file_id, drive_web_view_link, drive_folder_id, chunks_count, uploaded_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, user_email, filename, file_size, drive_file_id, drive_web_view_link, drive_folder_id, chunks_count, now_str))
        conn.commit()
        doc_id = cursor.lastrowid
        return {
            "id": doc_id,
            "user_id": user_id,
            "user_email": user_email,
            "filename": filename,
            "file_size": file_size,
            "drive_file_id": drive_file_id,
            "drive_web_view_link": drive_web_view_link,
            "drive_folder_id": drive_folder_id,
            "chunks_count": chunks_count,
            "uploaded_at": now_str
        }
    finally:
        conn.close()

def list_user_documents(user_id: int) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM documents WHERE user_id = ? ORDER BY id DESC", (user_id,))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

def list_all_documents() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        SELECT d.*, u.full_name as user_full_name 
        FROM documents d 
        JOIN users u ON d.user_id = u.id 
        ORDER BY d.id DESC
        """)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

# --- Custom Strategy Chunks Operations ---
def save_document_chunks(
    doc_id: int,
    user_id: int,
    user_email: str,
    chunks: List[Dict[str, Any]]
) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.utcnow().isoformat()
    count = 0
    try:
        for idx, ch in enumerate(chunks):
            title = ch.get("title") or ch.get("question") or f"Strategy Chunk #{idx+1}"
            text_content = ch.get("text") or ch.get("full_text") or ch.get("pitch") or ch.get("strategy_pitch") or ""
            strategy_pitch = ch.get("pitch") or ch.get("strategy_pitch") or ch.get("response") or text_content
            context = ch.get("context") or "Custom sales closing strategy."

            cursor.execute("""
            INSERT INTO document_chunks (doc_id, user_id, user_email, chunk_index, title, text_content, strategy_pitch, context, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
            """, (doc_id, user_id, user_email, idx, title, text_content, strategy_pitch, context, now_str, now_str))
            count += 1

        # Update document chunk count
        cursor.execute("UPDATE documents SET chunks_count = ? WHERE id = ?", (count, doc_id))
        conn.commit()
        return count
    finally:
        conn.close()

def list_user_chunks(user_id: int, doc_id: Optional[int] = None) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if doc_id:
            cursor.execute("SELECT * FROM document_chunks WHERE user_id = ? AND doc_id = ? ORDER BY chunk_index ASC", (user_id, doc_id))
        else:
            cursor.execute("SELECT * FROM document_chunks WHERE user_id = ? ORDER BY id DESC", (user_id,))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

def list_all_active_chunks_for_user(user_id: int) -> List[Dict[str, Any]]:
    """Retrieves all active chunks belonging to this user for vector indexing."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM document_chunks WHERE user_id = ? AND is_active = 1", (user_id,))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

def update_chunk(chunk_id: int, user_id: int, title: str, strategy_pitch: str, context: Optional[str] = None, is_active: int = 1) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.utcnow().isoformat()
    try:
        cursor.execute("""
        UPDATE document_chunks 
        SET title = ?, strategy_pitch = ?, context = COALESCE(?, context), is_active = ?, updated_at = ?
        WHERE id = ? AND user_id = ?
        """, (title, strategy_pitch, context, is_active, now_str, chunk_id, user_id))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()

def delete_chunk(chunk_id: int, user_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM document_chunks WHERE id = ? AND user_id = ?", (chunk_id, user_id))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()

# Initialize DB when module loaded
init_db()
