# ARCHITEKT — Adaptive Technical Mastery Quiz Platform

## 1. Product Definition
**Goal:** To accelerate technical fluency through active recall and spaced repetition. The platform presents scenario-based, multiple-choice, and definition questions across technical domains. It tracks correctness, speed, and topic-level mastery, then surfaces weak areas for reinforcement.

This is a personal technical learning tool built to learn systems design, solutions architecture, software architecture, backend engineering, APIs, DevOps, automation, and AI concepts.

## 2. System Architecture
ARCHITEKT follows a strict 4-layer architecture:
- **Presentation:** React SPA (PWA) client.
- **Application:** FastAPI routing and application coordination.
- **Domain:** Pure business logic containing deterministic mastery state, evaluation rules, and adaptive selection.
- **Infrastructure:** PostgreSQL via SQLAlchemy, alembic migrations, JWT tokens.

## 3. The Backend Engine (Phase 2)
The backend enforces a strict deterministic learning engine:
- **Answer Evaluation:** Correctness + response time evaluated heavily (e.g. correct under 20s = STRONG signal).
- **Mastery State Machine:** Six strictly defined states: `UNSEEN → ATTEMPTED → STRUGGLING → DEVELOPING → COMPETENT → MASTERED`.
- **Adaptive Selector:** Surfaces questions using a formula combining: `(Weakness Weight × 0.50) + (Days Since Seen × 0.30) + (Difficulty Match × 0.20)`.

## 4. Phase 3 & Beyond (Hybrid Offline Setup)
ARCHITEKT is an **Offline-First PWA** powered by:
- IndexedDB + Service Workers caching approved questions.
- Idempotent backend synchronization logic (`client_attempt_id`), recalculating mastery profiles server-side upon reconnect.

## Running the Application
Ensure Postgres is running locally on port `5432`.

### 1. Database & Backend Setup:
```powershell
cd architekt-backend
.\venv\Scripts\activate
pip install -r requirements.txt

# Apply the latest Offline PWA Sync tables:
alembic upgrade head

# Seed 50 questions (only run once):
python scripts/seed_questions.py

# Start the FastAPI engine:
uvicorn app.main:app --reload
```
The backend will boot on `http://127.0.0.1:8000`.

### 2. Frontend React PWA:
Open a second terminal:
```powershell
cd architekt-frontend
npm install
npm run dev
```
Navigate to `http://localhost:5173` in your browser. The frontend is fully indexed for offline-compatibility.
