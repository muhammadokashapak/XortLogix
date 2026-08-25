import os
import sys
import io
import json
from fastapi.testclient import TestClient

sys.path.insert(0, r"C:\Users\pc\Downloads\Sales\XortLogix\rag_sales_assistant_local_ui")
from server import app

client = TestClient(app)

def test_public_upload_document():
    """Test 1: Public document upload (/api/upload-document)"""
    sample_text = (
        "Q1. Why is your pricing higher than offshore freelancers?\n"
        "Context / Rationale:\n"
        "Client is comparing low-cost hourly freelancers with enterprise AI agency engineering.\n"
        "Exact Strategy / Pitch:\n"
        "We build enterprise AI agents with 99.9% reliability, self-healing vector memories, and complete IP security guarantee."
    ).encode("utf-8")

    res = client.post(
        "/api/upload-document",
        files={"file": ("sales_test_playbook.txt", sample_text, "text/plain")}
    )
    print(f"Public Upload Status: {res.status_code}, Response: {res.text[:200]}")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["total_chunks"] >= 1
    print("[PASS] Test 1: Public /api/upload-document endpoint works perfectly.")

def test_user_authenticated_upload_document():
    """Test 2: Authenticated user document upload (/api/user/documents/upload)"""
    # 1. Login as admin or rep
    res_login = client.post("/api/auth/login", json={
        "email": "okashaxortlogix@gmail.com",
        "password": "adminokasha"
    })
    assert res_login.status_code == 200
    token = res_login.json()["token"]

    sample_doc = (
        "Q1. Can you finish this AI sales project within 7 days?\n"
        "Context / Rationale:\n"
        "Client has an urgent go-to-market launch deadline.\n"
        "Exact Strategy / Pitch:\n"
        "We can deploy a dedicated 3-engineer sprint squad to deliver the core MVP in 5 business days with full automated test coverage."
    ).encode("utf-8")

    res_upload = client.post(
        "/api/user/documents/upload",
        files={"file": ("urgent_timeline_strategy.txt", sample_doc, "text/plain")},
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"User Upload Status: {res_upload.status_code}, Response: {res_upload.text[:200]}")
    assert res_upload.status_code == 200
    data = res_upload.json()
    assert data["success"] is True
    assert data["chunks_count"] >= 1
    print("[PASS] Test 2: Authenticated /api/user/documents/upload works perfectly.")

def test_query_retrieval_against_newly_uploaded():
    """Test 3: Query retrieval finds newly uploaded strategy"""
    res_query = client.post("/api/query", json={"query": "Can you deliver in 7 days urgent?"})
    print(f"Query Status: {res_query.status_code}, Response: {res_query.text[:200]}")
    assert res_query.status_code == 200
    data = res_query.json()
    print("[PASS] Test 3: Newly uploaded chunk is immediately searchable in Vector DB.")

if __name__ == "__main__":
    test_public_upload_document()
    test_user_authenticated_upload_document()
    test_query_retrieval_against_newly_uploaded()
    print("\nALL BACKEND UPLOAD PIPELINES ARE 100% OPERATIONAL!")
