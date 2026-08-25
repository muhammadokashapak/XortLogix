"""
Continuous Live Upload & Vector Chunking Test Engine
Runs live loopback tests against the running Sales Assistant server (http://127.0.0.1:8000)
or directly via FastAPI TestClient.
"""

import sys
import time
import requests
import json

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

SERVER_URL = "http://127.0.0.1:8000"

def run_live_test_iteration(iteration_num=1):
    print(f"\n==================================================================")
    print(f" 🧪 [LIVE TEST #{iteration_num}] TESTING UPLOAD & VECTOR EMBEDDING PIPELINE")
    print(f"==================================================================")

    test_content = (
        f"Q{iteration_num}. Why choose XortLogix over other AI consulting firms?\n"
        f"Context / Rationale:\n"
        f"Client evaluating enterprise engineering pedigree, risk mitigation, and security.\n"
        f"Exact Strategy / Pitch:\n"
        f"We build enterprise AI agents with 99.9% reliability, sub-second latency, self-healing vector memories, and full IP transfer (Test Run #{iteration_num})."
    )

    # 1. Test Server Health
    try:
        res_health = requests.get(f"{SERVER_URL}/api/knowledge-status", timeout=5)
        print(f" [+] Server Health: {res_health.status_code} OK | Active Doc: {res_health.json().get('active_document')}")
    except Exception as e:
        print(f" [!] Server connection note: {e}. Testing via TestClient directly...")
        from fastapi.testclient import TestClient
        from server import app
        tc = TestClient(app)
        
        # Test 1: Upload document
        res_up = tc.post(
            "/api/upload-document",
            files={"file": (f"automated_test_playbook_{iteration_num}.txt", test_content.encode("utf-8"), "text/plain")}
        )
        assert res_up.status_code == 200, f"Upload failed: {res_up.text}"
        data = res_up.json()
        print(f" [PASS] 1. File Uploaded: {data.get('filename')} | Total Chunks: {data.get('total_chunks')}")

        # Test 2: Verify Knowledge Status
        res_st = tc.get("/api/knowledge-status")
        assert res_st.status_code == 200
        print(f" [PASS] 2. Knowledge Status Active: {res_st.json().get('active_document')}")

        # Test 3: Query Retrieval against new chunk
        res_q = tc.post("/api/query", json={"query": "Why choose XortLogix over others?"})
        assert res_q.status_code == 200
        print(f" [PASS] 3. Vector ChromaDB Query Success: '{res_q.json().get('response', '')[:90]}...'")
        return True

    # If Live Server is responding via HTTP:
    files = {"file": (f"automated_test_playbook_{iteration_num}.txt", test_content.encode("utf-8"), "text/plain")}
    res_up = requests.post(f"{SERVER_URL}/api/upload-document", files=files, timeout=10)
    print(f" [+] Upload Status: {res_up.status_code}")
    assert res_up.status_code == 200, f"Upload failed: {res_up.text}"
    data = res_up.json()
    print(f" [PASS] 1. File Uploaded: {data.get('filename')} | Total Chunks: {data.get('total_chunks')}")

    # Query Retrieval
    res_q = requests.post(f"{SERVER_URL}/api/query", json={"query": "Why choose XortLogix over others?"}, timeout=10)
    assert res_q.status_code == 200
    print(f" [PASS] 2. ChromaDB Vector Retrieval: '{res_q.json().get('response', '')[:90]}...'")

    print(f" ✅ ALL PIPELINE TESTS PASSED FOR RUN #{iteration_num}!")
    return True

if __name__ == "__main__":
    runs = 3
    for i in range(1, runs + 1):
        success = run_live_test_iteration(i)
        time.sleep(1)
    print("\n🎉 Continuous Live Testing Complete: 3/3 Runs Succeeded with 0 Errors!")
