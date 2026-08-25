import os
import sys
import json
from fastapi.testclient import TestClient

sys.path.insert(0, r"C:\Users\pc\Downloads\Sales\XortLogix\rag_sales_assistant_local_ui")
from server import app
import models_db

client = TestClient(app)

def test_admin_seed_and_login():
    """1. Test that default Admin account (okashaxortlogix@gmail.com / adminokasha) is seeded and can log in."""
    res = client.post("/api/auth/login", json={
        "email": "okashaxortlogix@gmail.com",
        "password": "adminokasha"
    })
    assert res.status_code == 200, f"Admin login failed: {res.text}"
    data = res.json()
    assert data["success"] is True
    assert "token" in data
    assert data["user"]["role"] == "admin"
    assert data["user"]["email"] == "okashaxortlogix@gmail.com"
    print("[PASS] Test 1: Admin seed login successful with role='admin'.")

def test_sales_rep_registration_and_rbac_guards():
    """2. Test that a sales rep registers and is blocked from admin routes (403 Forbidden)."""
    # Register a new sales rep
    rep_email = f"rep_{os.urandom(4).hex()}@xortlogix.com"
    res_reg = client.post("/api/auth/register", json={
        "email": rep_email,
        "password": "reppassword123",
        "full_name": "Hamza Tariq (Sales Rep)"
    })
    assert res_reg.status_code == 200, f"Registration failed: {res_reg.text}"
    rep_data = res_reg.json()
    rep_token = rep_data["token"]
    assert rep_data["user"]["role"] == "user"

    # Rep tries to access Admin Overview -> Must get 403 Forbidden
    res_admin_guard = client.get("/api/admin/overview", headers={
        "Authorization": f"Bearer {rep_token}"
    })
    assert res_admin_guard.status_code == 403, f"Expected 403 Forbidden, got {res_admin_guard.status_code}"

    # Admin accesses Admin Overview -> Must get 200 OK
    res_login_admin = client.post("/api/auth/login", json={
        "email": "okashaxortlogix@gmail.com",
        "password": "adminokasha"
    })
    admin_token = res_login_admin.json()["token"]
    res_admin_ok = client.get("/api/admin/overview", headers={
        "Authorization": f"Bearer {admin_token}"
    })
    assert res_admin_ok.status_code == 200
    overview_data = res_admin_ok.json()
    assert "total_users" in overview_data
    assert "gdrive_integration" in overview_data
    print("[PASS] Test 2: RBAC role authorization properly enforces 403 for standard users and grants 200 for admins.")

def test_user_document_upload_and_chunk_management():
    """3. Test document upload (Drive + Vector pipeline) and custom chunk editing."""
    rep_email = f"salesrep_{os.urandom(4).hex()}@xortlogix.com"
    res_reg = client.post("/api/auth/register", json={
        "email": rep_email,
        "password": "password123",
        "full_name": "Ali Raza"
    })
    rep_token = res_reg.json()["token"]

    # Sample strategy document content
    doc_content = (
        "Q1. Why are your AI automation rates higher than standard offshore rates?\n"
        "Context / Rationale:\n"
        "Client is comparing specialized AI engineering with basic script development.\n"
        "Exact Strategy / Pitch:\n"
        "We build enterprise LLM workflows with deterministic validation, self-healing memory, and zero hallucination safeguards."
    ).encode("utf-8")

    # Upload strategy document
    res_upload = client.post(
        "/api/user/documents/upload",
        files={"file": ("custom_ai_playbook.txt", doc_content, "text/plain")},
        headers={"Authorization": f"Bearer {rep_token}"}
    )
    assert res_upload.status_code == 200, f"Upload failed: {res_upload.text}"
    upload_data = res_upload.json()
    assert upload_data["success"] is True
    assert upload_data["chunks_count"] >= 1
    assert "drive_backup" in upload_data
    assert "web_view_link" in upload_data["drive_backup"]

    # List user chunks
    res_chunks = client.get("/api/user/chunks", headers={"Authorization": f"Bearer {rep_token}"})
    assert res_chunks.status_code == 200
    chunks_list = res_chunks.json()["chunks"]
    assert len(chunks_list) >= 1
    chunk_id = chunks_list[0]["id"]

    # Edit chunk
    res_edit = client.put(
        f"/api/user/chunks/{chunk_id}",
        json={
            "title": "Why are your AI automation rates higher?",
            "strategy_pitch": "Updated Pitch: Our enterprise AI architectures guarantee 99.9% uptime and zero data leakage.",
            "context": "Enterprise architecture objection."
        },
        headers={"Authorization": f"Bearer {rep_token}"}
    )
    assert res_edit.status_code == 200
    print("[PASS] Test 3: User document upload, Drive backup simulation, and Custom Chunk manager work seamlessly.")

if __name__ == "__main__":
    test_admin_seed_and_login()
    test_sales_rep_registration_and_rbac_guards()
    test_user_document_upload_and_chunk_management()
    print("\nALL MULTI-TENANT RBAC & GOOGLE DRIVE TESTS COMPLETED SUCCESSFULLY!")
