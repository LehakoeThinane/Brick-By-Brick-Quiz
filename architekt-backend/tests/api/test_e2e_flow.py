import pytest
from httpx import AsyncClient
from app.main import app
from app.models.enums import QuizMode

# Note: This test requires a running PostgreSQL database configured in your test environment.

@pytest.mark.asyncio
async def test_e2e_flow():
    # 1. Register and Login
    async with AsyncClient(app=app, base_url="http://test") as ac:
        register_payload = {
            "email": "tester_e2e@example.com",
            "password": "strongPassword123"
        }
        res_register = await ac.post("/auth/register", json=register_payload)
        # Assuming HTTP 201 Created or 200 OK
        assert res_register.status_code in (200, 201), f"Register failed: {res_register.text}"
        
        login_payload = {
            "username": "tester_e2e@example.com",
            "password": "strongPassword123"
        }
        res_login = await ac.post("/auth/token", data=login_payload)
        assert res_login.status_code == 200, f"Login failed: {res_login.text}"
        token = res_login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Create Session
        session_payload = {
            "mode": QuizMode.CATEGORY,
            # using an empty category_slug means 'all categories' or depends on validation
            # we assume 'systems-design' exists if seeds are run
            "category_slug": "systems-design" 
        }
        res_session = await ac.post("/sessions", json=session_payload, headers=headers)
        if res_session.status_code == 404:
             pytest.skip("Test data not seeded, cannot proceed with E2E session tests.")
        assert res_session.status_code == 200, res_session.text
        session_id = res_session.json()["id"]
        
        # 3. Next Question
        res_next_q = await ac.post(f"/sessions/{session_id}/next", headers=headers)
        if res_next_q.status_code == 404:
             pytest.skip("No questions available to test.")
        assert res_next_q.status_code == 200
        question_id = res_next_q.json()["id"]
        
        # 4. Submit Answer
        answer_payload = {
            "question_id": question_id,
            "selected_option": "A",
            "response_time_ms": 15000
        }
        res_answer = await ac.post(f"/sessions/{session_id}/answer", json=answer_payload, headers=headers)
        assert res_answer.status_code == 200
        eval_result = res_answer.json()
        assert "is_correct" in eval_result
        assert "mastery_signal" in eval_result
        
        # 5. Check Results (Complete Session)
        res_complete = await ac.post(f"/sessions/{session_id}/complete", headers=headers)
        assert res_complete.status_code == 200
        results = res_complete.json()
        assert "score" in results
        
        # 6. Review Queue
        res_review = await ac.get("/review-queue", headers=headers)
        assert res_review.status_code == 200
        assert isinstance(res_review.json(), list)
