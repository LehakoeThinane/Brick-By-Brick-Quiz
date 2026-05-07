"""Adds 12 more questions to push total past 150."""
import sys, uuid
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.category import Category
from app.models.question import Question

EXTRA = [
    {
        "category_slug": "systems-design",
        "subcategory": "Networking",
        "tags": ["OSI Model"],
        "difficulty": 2,
        "question_type": "identification",
        "question_text": "At which OSI layer does TCP operate, providing reliable ordered delivery?",
        "options": {"A": "Layer 2 — Data Link", "B": "Layer 3 — Network", "C": "Layer 4 — Transport", "D": "Layer 7 — Application"},
        "correct_answer": "C",
        "explanation": "The Transport layer (Layer 4) manages end-to-end communication, flow control, and reliability. TCP and UDP both live here. IP lives at Layer 3; HTTP at Layer 7.",
        "hint": "TCP/UDP both live at the same OSI layer.",
    },
    {
        "category_slug": "systems-design",
        "subcategory": "Databases",
        "tags": ["Time-Series"],
        "difficulty": 3,
        "question_type": "identification",
        "question_text": "Which database type is optimised for storing data points indexed by time, such as server metrics or IoT sensor readings?",
        "options": {"A": "Relational (PostgreSQL)", "B": "Document store (MongoDB)", "C": "Time-series (InfluxDB, TimescaleDB)", "D": "Graph database (Neo4j)"},
        "correct_answer": "C",
        "explanation": "Time-series databases store timestamp-value pairs and optimise for range queries, downsampling, and retention policies. They use columnar compression that exploits temporal locality for 10-100x storage savings versus row-based stores.",
        "hint": "The name of the category is a direct clue.",
    },
    {
        "category_slug": "systems-design",
        "subcategory": "Architecture",
        "tags": ["Leader Election"],
        "difficulty": 4,
        "question_type": "definition",
        "question_text": "Why is Leader Election necessary in distributed systems like Kafka or etcd?",
        "options": {
            "A": "To balance CPU load evenly across all nodes.",
            "B": "To designate one node as the authoritative coordinator for writes, preventing split-brain conflicts.",
            "C": "To encrypt inter-node traffic using a shared key.",
            "D": "To assign unique IDs to messages in a queue.",
        },
        "correct_answer": "B",
        "explanation": "Without a single leader, multiple nodes may independently accept conflicting writes (split-brain). Algorithms like Raft and Paxos elect one leader that serialises decisions; other nodes replicate from it.",
        "hint": "Without a single decision-maker, who resolves conflicts?",
    },
    {
        "category_slug": "backend-engineering",
        "subcategory": "Database",
        "tags": ["Migrations"],
        "difficulty": 2,
        "question_type": "scenario",
        "question_text": "You must add a NOT NULL column to a 50-million-row production table without downtime. What is the safest approach?",
        "options": {
            "A": "Add the column as NOT NULL with a DEFAULT value; the DB records the default in metadata and backfills lazily.",
            "B": "Drop the table, add the column, and re-import from backup.",
            "C": "Add the column inside a single transaction that holds a table lock until backfill completes.",
            "D": "NOT NULL columns cannot be added to existing tables.",
        },
        "correct_answer": "A",
        "explanation": "PostgreSQL 11+ adds NOT NULL columns with a DEFAULT instantly by storing the default in metadata — no full table rewrite. Rows are backfilled lazily on access, avoiding a prolonged lock.",
        "hint": "Modern databases can defer backfill — use a DEFAULT to avoid the lock.",
    },
    {
        "category_slug": "backend-engineering",
        "subcategory": "Architecture",
        "tags": ["Rate Limiting", "Distributed"],
        "difficulty": 3,
        "question_type": "scenario",
        "question_text": "You run 10 API servers each with their own in-memory rate-limit counter. A user sends 9 requests to server 1 and 9 to server 2, bypassing a 10 req/min limit. What is the fix?",
        "options": {
            "A": "Increase the per-server limit so individual servers rarely trigger it.",
            "B": "Use a centralised counter in Redis that all instances increment atomically.",
            "C": "Sticky sessions so each user always hits the same server.",
            "D": "Rate limit at the DNS level instead.",
        },
        "correct_answer": "B",
        "explanation": "Distributed rate limiting requires a shared atomic counter visible to all instances. Redis with atomic INCR and TTL is the standard solution. Sticky sessions partially help but fail when servers restart or users switch networks.",
        "hint": "Local counters are invisible to other servers — share state centrally.",
    },
    {
        "category_slug": "apis",
        "subcategory": "Security",
        "tags": ["mTLS"],
        "difficulty": 4,
        "question_type": "definition",
        "question_text": "What does mTLS (Mutual TLS) add over standard TLS for inter-service communication?",
        "options": {
            "A": "It compresses traffic in addition to encrypting it.",
            "B": "Both client and server present certificates, so each verifies the other's identity — not just the server proving itself.",
            "C": "It replaces JWT tokens for user authentication.",
            "D": "It enables HTTP/2 for all microservice connections.",
        },
        "correct_answer": "B",
        "explanation": "Standard TLS: client verifies the server's certificate. mTLS: the server also verifies the client's certificate. This provides cryptographic service-to-service identity used heavily in zero-trust service meshes.",
        "hint": "Mutual = both sides prove who they are.",
    },
    {
        "category_slug": "apis",
        "subcategory": "REST",
        "tags": ["HATEOAS"],
        "difficulty": 4,
        "question_type": "definition",
        "question_text": "What does HATEOAS (Hypermedia As The Engine Of Application State) add to a REST API response?",
        "options": {
            "A": "HTML rendering instructions for the client UI.",
            "B": "Links in the response body that tell the client what actions and related resources are available next, so clients never hardcode URLs.",
            "C": "Automatic caching headers for CDN optimisation.",
            "D": "Binary encoding of JSON responses to reduce payload size.",
        },
        "correct_answer": "B",
        "explanation": "HATEOAS is the highest REST maturity level. Responses include _links (self, next, cancel) so clients discover capabilities dynamically by following links — like a browser following hyperlinks — rather than relying on hardcoded endpoint paths.",
        "hint": "Hyper-media means the response contains links to drive next steps.",
    },
    {
        "category_slug": "devops",
        "subcategory": "Containers",
        "tags": ["Kubernetes", "Services"],
        "difficulty": 2,
        "question_type": "definition",
        "question_text": "What is a Kubernetes Service and why is it needed when Pods already have IP addresses?",
        "options": {
            "A": "A Service is the Kubernetes term for a container image in a registry.",
            "B": "A Service provides a stable DNS name and IP that routes to a dynamic set of Pods, abstracting away their ephemeral IPs that change on restart.",
            "C": "A Service allocates persistent storage volumes to Pods.",
            "D": "A Service runs health checks and restarts failed Pods automatically.",
        },
        "correct_answer": "B",
        "explanation": "Pods are ephemeral — when they restart or scale, their IPs change. A Kubernetes Service gets a stable ClusterIP and DNS name and uses label selectors to route to matching Pods. This is Kubernetes' built-in service discovery.",
        "hint": "Pod IPs are temporary; Service IPs are stable. Which do clients use?",
    },
    {
        "category_slug": "ai-concepts",
        "subcategory": "LLMs",
        "tags": ["Tokens", "Tokenization"],
        "difficulty": 1,
        "question_type": "definition",
        "question_text": "In LLMs, what is a token and why does its count matter for API cost and context window limits?",
        "options": {
            "A": "A token is a single character; a 1,000-character input uses exactly 1,000 tokens.",
            "B": "A token is a chunk of text (roughly 3-4 characters); API pricing and context window limits are measured in tokens, not characters.",
            "C": "A token is a cryptographic key used for API authentication.",
            "D": "A token represents one complete sentence in the model vocabulary.",
        },
        "correct_answer": "B",
        "explanation": "LLMs tokenise text into subword chunks using BPE or SentencePiece. 'unhappiness' might be 3 tokens. API costs are billed per 1,000 tokens in/out, and context window limits (e.g., 128k tokens) determine how much text the model can process at once.",
        "hint": "It is between a character and a word in size.",
    },
    {
        "category_slug": "java-mastery",
        "subcategory": "7. Tools & Technologies",
        "tags": ["Gradle", "Build"],
        "difficulty": 2,
        "question_type": "tradeoff",
        "question_text": "What advantage does Gradle offer over Maven for large Java projects?",
        "options": {
            "A": "Gradle uses XML, making it easier to read than Maven YAML.",
            "B": "Gradle uses a Groovy/Kotlin DSL with incremental builds that only recompile changed modules, making large projects significantly faster.",
            "C": "Gradle supports more programming languages than Maven.",
            "D": "Gradle has built-in Docker integration; Maven does not.",
        },
        "correct_answer": "B",
        "explanation": "Maven rebuilds all modules in order regardless of what changed. Gradle tracks task inputs/outputs and skips tasks whose inputs are unchanged. For a 200-module project this can reduce build time from 10 minutes to under a minute.",
        "hint": "Incremental = only rebuild what changed.",
    },
    {
        "category_slug": "sql-roadmap",
        "subcategory": "5. Data Engineering / Backend Integration",
        "tags": ["CTEs", "SQL"],
        "difficulty": 3,
        "question_type": "definition",
        "question_text": "What is a Common Table Expression (CTE) in SQL and when is it preferred over a subquery?",
        "options": {
            "A": "A CTE is a temporary table permanently stored in the database.",
            "B": "A CTE is a named temporary result set defined with the WITH clause, making complex queries more readable and enabling recursive queries.",
            "C": "CTEs are always faster than subqueries in all databases.",
            "D": "A CTE stores aggregated results in a cache reused across sessions.",
        },
        "correct_answer": "B",
        "explanation": "WITH name AS (...) SELECT ... names a subquery for readability and reuse. Recursive CTEs (WITH RECURSIVE) are the SQL standard way to traverse hierarchical data such as org charts and file systems.",
        "hint": "WITH keyword — think of it as naming a subquery for clarity.",
    },
    {
        "category_slug": "python-roadmap",
        "subcategory": "3. Understand DSA",
        "tags": ["Binary Search", "Complexity"],
        "difficulty": 2,
        "question_type": "identification",
        "question_text": "What is the time complexity of binary search on a sorted list of N elements?",
        "options": {
            "A": "O(n) — the list must be sorted.",
            "B": "O(log n) — the list must be sorted.",
            "C": "O(log n) — the list can be unsorted.",
            "D": "O(1) — the list must be stored in a hash map.",
        },
        "correct_answer": "B",
        "explanation": "Binary search halves the search space each step, giving O(log n). It requires the input to be sorted. For 1 billion elements, binary search takes about 30 comparisons versus 1 billion for linear search.",
        "hint": "Each step eliminates half — how many halvings reach 1?",
    },
]


def main():
    db = SessionLocal()
    try:
        cats = {c.slug: c.id for c in db.execute(select(Category)).scalars().all()}
        inserted = 0
        for q in EXTRA:
            if db.execute(select(Question).where(Question.question_text == q["question_text"])).scalar_one_or_none():
                continue
            db.add(Question(
                id=uuid.uuid4(),
                category_id=cats[q["category_slug"]],
                subcategory=q["subcategory"],
                tags=q.get("tags", []),
                difficulty=q["difficulty"],
                question_type=q["question_type"],
                question_text=q["question_text"],
                options=q["options"],
                correct_answer=q["correct_answer"],
                explanation=q["explanation"],
                hint=q.get("hint", ""),
                related_concepts=[],
                source="manual",
                review_status="approved",
                times_answered=0,
                times_correct=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ))
            inserted += 1
        db.commit()
        print(f"Inserted {inserted} extra questions.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
