"""
Purges auto-generated placeholder questions from the DB and re-seeds with real ones.
Safe to run multiple times — checks for existing text before inserting.
"""
import sys, uuid
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dotenv import load_dotenv
load_dotenv()

import uuid as uuid_mod
from sqlalchemy import select, delete as sql_delete
from app.db.session import SessionLocal
from app.models.category import Category
from app.models.question import Question
from app.models.answer_attempt import AnswerAttempt
from app.models.review_queue import ReviewQueue
from app.models.enums import QuestionType, ReviewStatus, QuestionSource

# ---------------------------------------------------------------------------
# Real questions for the 4 roadmap categories (replaces the auto-generated ones)
# ---------------------------------------------------------------------------

ROADMAP_QUESTIONS = [

    # ── Python Roadmap ──────────────────────────────────────────────────────
    {
        "category_slug": "python-roadmap",
        "subcategory": "1. Basics First",
        "tags": ["Python Basics", "Syntax"],
        "difficulty": 1,
        "question_type": QuestionType.DEFINITION,
        "question_text": "What does a Python list comprehension `[x*2 for x in range(5)]` produce?",
        "options": {"A": "[0, 2, 4, 6, 8]", "B": "[0, 1, 2, 3, 4]", "C": "[2, 4, 6, 8, 10]", "D": "[1, 2, 3, 4, 5]"},
        "correct_answer": "A",
        "explanation": "range(5) produces 0,1,2,3,4. Multiplying each by 2 gives 0,2,4,6,8. List comprehensions are a concise, idiomatic Python way to build lists.",
        "hint": "range(5) starts at 0, not 1.",
    },
    {
        "category_slug": "python-roadmap",
        "subcategory": "2. Master Core Python",
        "tags": ["Dunder Methods", "OOP"],
        "difficulty": 2,
        "question_type": QuestionType.DEFINITION,
        "question_text": "What is the difference between `__str__` and `__repr__` in Python?",
        "options": {
            "A": "__str__ is for developers (debugging), __repr__ is for end-users.",
            "B": "__repr__ is for developers (unambiguous), __str__ is for end-users (readable).",
            "C": "They are identical; Python uses them interchangeably.",
            "D": "__repr__ can only return integers."
        },
        "correct_answer": "B",
        "explanation": "`__repr__` should return an unambiguous string representation useful for debugging. `__str__` should return a human-friendly string. If only `__repr__` is defined, it also serves as the fallback for `__str__`.",
        "hint": "Think: repr = reproducible, str = readable.",
    },
    {
        "category_slug": "python-roadmap",
        "subcategory": "3. Understand DSA",
        "tags": ["Data Structures", "Complexity"],
        "difficulty": 2,
        "question_type": QuestionType.IDENTIFICATION,
        "question_text": "Which Python built-in data structure provides O(1) average-case lookup by key?",
        "options": {"A": "list", "B": "tuple", "C": "dict", "D": "deque"},
        "correct_answer": "C",
        "explanation": "Python dicts are hash maps. A hash function maps keys to buckets, allowing O(1) average lookups. Lists require O(n) linear search unless sorted and binary-searched.",
        "hint": "Hash maps underpin Python's most-used data structure.",
    },
    {
        "category_slug": "python-roadmap",
        "subcategory": "4. Database Knowledge",
        "tags": ["SQLAlchemy", "ORM"],
        "difficulty": 3,
        "question_type": QuestionType.SCENARIO,
        "question_text": "In SQLAlchemy, you run `db.query(User).filter(User.id == user_id).first()`. The query runs but returns `None` even though the row exists. What is the most likely cause?",
        "options": {
            "A": "SQLAlchemy does not support `.first()`.",
            "B": "The session was not committed after the INSERT, so the row is invisible to this query.",
            "C": "The User model is missing a primary key.",
            "D": "`.filter()` requires two arguments."
        },
        "correct_answer": "B",
        "explanation": "SQLAlchemy sessions use transactions. If the INSERT was never committed (or the session was not flushed), the row does not exist in the database snapshot visible to subsequent queries in other sessions.",
        "hint": "Database transactions must be committed to be visible outside the current session.",
    },
    {
        "category_slug": "python-roadmap",
        "subcategory": "5. Learn Backend / Specialization",
        "tags": ["FastAPI", "Decorators"],
        "difficulty": 3,
        "question_type": QuestionType.DEFINITION,
        "question_text": "In FastAPI, what does the `@app.get('/items/{item_id}')` decorator do?",
        "options": {
            "A": "It marks the function as a background task.",
            "B": "It registers the function as the HTTP GET handler for the `/items/{item_id}` path.",
            "C": "It validates that `item_id` is always a string.",
            "D": "It caches the response automatically."
        },
        "correct_answer": "B",
        "explanation": "FastAPI's path operation decorators (`@app.get`, `@app.post`, etc.) bind a Python function to an HTTP method and URL path. FastAPI also automatically validates path parameters using type hints.",
        "hint": "Decorators in Python wrap functions — here they register a route.",
    },
    {
        "category_slug": "python-roadmap",
        "subcategory": "6. Build Projects",
        "tags": ["Virtual Environments", "Dependencies"],
        "difficulty": 1,
        "question_type": QuestionType.DEFINITION,
        "question_text": "What is the primary purpose of a Python virtual environment (`venv`)?",
        "options": {
            "A": "To run Python code inside a Docker container.",
            "B": "To isolate project dependencies so different projects don't conflict with each other.",
            "C": "To speed up Python execution by caching bytecode.",
            "D": "To encrypt Python source files."
        },
        "correct_answer": "B",
        "explanation": "A `venv` creates an isolated directory containing a Python interpreter and its own `site-packages`. This prevents version conflicts between projects that require different versions of the same library.",
        "hint": "Two projects needing different versions of the same library would conflict globally.",
    },
    {
        "category_slug": "python-roadmap",
        "subcategory": "7. Tools & Technologies",
        "tags": ["Testing", "pytest"],
        "difficulty": 2,
        "question_type": QuestionType.SCENARIO,
        "question_text": "Which pytest feature lets you run the same test function with multiple sets of input/output pairs without copy-pasting it?",
        "options": {
            "A": "@pytest.fixture",
            "B": "@pytest.mark.parametrize",
            "C": "@pytest.mark.skip",
            "D": "pytest.raises()"
        },
        "correct_answer": "B",
        "explanation": "`@pytest.mark.parametrize` allows a single test function to be called with multiple argument sets, each running as an independent test case — reducing repetition significantly.",
        "hint": "The name literally means 'give it many parameters'.",
    },
    {
        "category_slug": "python-roadmap",
        "subcategory": "8. Advanced Concepts",
        "tags": ["GIL", "Concurrency"],
        "difficulty": 4,
        "question_type": QuestionType.TRADEOFF,
        "question_text": "Python's Global Interpreter Lock (GIL) prevents true parallelism for CPU-bound threads. Which module bypasses the GIL entirely for CPU-intensive work?",
        "options": {
            "A": "threading",
            "B": "asyncio",
            "C": "multiprocessing",
            "D": "concurrent.futures.ThreadPoolExecutor"
        },
        "correct_answer": "C",
        "explanation": "`multiprocessing` spawns separate OS processes, each with its own Python interpreter and GIL. This achieves true CPU parallelism. `threading` and `ThreadPoolExecutor` are still bound by the GIL for CPU work.",
        "hint": "Separate processes = separate GILs.",
    },

    # ── JS/TS Roadmap ────────────────────────────────────────────────────────
    {
        "category_slug": "jsts-roadmap",
        "subcategory": "1. Basics First (Strong Foundation)",
        "tags": ["JavaScript", "Hoisting"],
        "difficulty": 1,
        "question_type": QuestionType.DEFINITION,
        "question_text": "What does JavaScript 'hoisting' mean for `var` declarations?",
        "options": {
            "A": "var declarations are moved to the bottom of the file.",
            "B": "var declarations (but not their assignments) are moved to the top of their scope before execution.",
            "C": "var variables are automatically assigned a value of 0.",
            "D": "var variables cannot be reassigned after declaration."
        },
        "correct_answer": "B",
        "explanation": "JavaScript moves `var` declarations to the top of their function/global scope before code runs, but not their assigned values. Accessing a hoisted `var` before assignment returns `undefined`, not a ReferenceError.",
        "hint": "Declaration is hoisted, initialisation is not.",
    },
    {
        "category_slug": "jsts-roadmap",
        "subcategory": "2. Master Core JS/TS",
        "tags": ["Closures", "Scope"],
        "difficulty": 3,
        "question_type": QuestionType.SCENARIO,
        "question_text": "A classic `for` loop with `var i` inside `setTimeout` prints the same final value of `i` every time. Changing `var` to `let` fixes it. Why?",
        "options": {
            "A": "let is faster than var.",
            "B": "let creates a new binding for each loop iteration (block scope), while var shares one binding across all iterations (function scope).",
            "C": "setTimeout behaves differently based on the variable keyword used.",
            "D": "let prevents the setTimeout from executing asynchronously."
        },
        "correct_answer": "B",
        "explanation": "`let` is block-scoped, so each iteration of the loop gets its own `i`. With `var`, all closures inside the loop share the same `i`, which has already incremented to its final value by the time the callbacks run.",
        "hint": "Block scope vs function scope is the key distinction.",
    },
    {
        "category_slug": "jsts-roadmap",
        "subcategory": "3. Understand DSA",
        "tags": ["Event Loop", "Async"],
        "difficulty": 3,
        "question_type": QuestionType.DEFINITION,
        "question_text": "In JavaScript's event loop, what is the difference between the Microtask Queue and the Macrotask (Callback) Queue?",
        "options": {
            "A": "Microtasks are for DOM events; Macrotasks are for network requests.",
            "B": "Microtasks (Promises, queueMicrotask) are processed before the next macrotask. Macrotasks (setTimeout, setInterval) run one per event loop tick.",
            "C": "They are identical; the names are interchangeable.",
            "D": "Macrotasks are always prioritised over Microtasks."
        },
        "correct_answer": "B",
        "explanation": "After each macrotask, the entire microtask queue is drained before the next macrotask begins. This is why Promise `.then()` callbacks always execute before a pending `setTimeout` callback.",
        "hint": "Promises resolve before timers fire.",
    },
    {
        "category_slug": "jsts-roadmap",
        "subcategory": "4. Database Knowledge",
        "tags": ["Prisma", "ORM"],
        "difficulty": 2,
        "question_type": QuestionType.IDENTIFICATION,
        "question_text": "What does Prisma's `schema.prisma` file primarily define?",
        "options": {
            "A": "The HTTP routes of the backend API.",
            "B": "The database connection, models (tables), and their relationships.",
            "C": "The frontend component structure.",
            "D": "Environment variable encryption keys."
        },
        "correct_answer": "B",
        "explanation": "The `schema.prisma` file is the single source of truth for your database schema in a Prisma project. It defines models (mapped to database tables), field types, relationships, and the database provider.",
        "hint": "It's the schema — the shape of your data.",
    },
    {
        "category_slug": "jsts-roadmap",
        "subcategory": "5. Learn Full-Stack Development",
        "tags": ["Next.js", "SSR"],
        "difficulty": 3,
        "question_type": QuestionType.TRADEOFF,
        "question_text": "What is the key difference between Server-Side Rendering (SSR) and Static Site Generation (SSG) in Next.js?",
        "options": {
            "A": "SSR generates HTML at build time; SSG generates it per request on the server.",
            "B": "SSG generates HTML at build time (faster, cacheable); SSR generates HTML on each request (slower, always fresh data).",
            "C": "SSR is only for API routes; SSG is for page components.",
            "D": "They produce identical output and have no performance difference."
        },
        "correct_answer": "B",
        "explanation": "SSG pre-builds pages at deploy time and serves static files — very fast but data can be stale. SSR runs server code per request — data is always current but adds server latency. Choose SSG for blogs, SSR for dashboards with real-time data.",
        "hint": "Build-time vs request-time.",
    },
    {
        "category_slug": "jsts-roadmap",
        "subcategory": "6. Build Projects",
        "tags": ["TypeScript", "Type Safety"],
        "difficulty": 2,
        "question_type": QuestionType.SCENARIO,
        "question_text": "TypeScript shows an error: `Argument of type 'string | undefined' is not assignable to parameter of type 'string'`. What is the cleanest way to resolve this?",
        "options": {
            "A": "Cast the value with `as string` everywhere.",
            "B": "Disable TypeScript's strict mode globally.",
            "C": "Narrow the type first: check `if (value !== undefined)` before using it.",
            "D": "Add `// @ts-ignore` on the offending line."
        },
        "correct_answer": "C",
        "explanation": "Type narrowing via a conditional check is the correct, safe approach. TypeScript understands that inside an `if (value !== undefined)` block, the type is `string`. Casting (`as string`) bypasses type safety and can cause runtime errors.",
        "hint": "Handle the undefined case explicitly rather than suppressing the error.",
    },
    {
        "category_slug": "jsts-roadmap",
        "subcategory": "7. Tools & Technologies",
        "tags": ["Vite", "Bundlers"],
        "difficulty": 2,
        "question_type": QuestionType.DEFINITION,
        "question_text": "Why is Vite significantly faster than Webpack during local development?",
        "options": {
            "A": "Vite uses Rust to compile JavaScript.",
            "B": "Vite skips bundling entirely in dev — it serves source files via native ESM and only transforms files on demand.",
            "C": "Vite caches the entire node_modules folder in RAM.",
            "D": "Vite pre-compiles TypeScript to Assembly."
        },
        "correct_answer": "B",
        "explanation": "Vite leverages native ES Modules in the browser. In dev mode, it skips the full bundle step — the browser requests individual files, and Vite transforms only what's needed on the fly. This makes cold starts instant for large projects.",
        "hint": "No bundle = instant start.",
    },
    {
        "category_slug": "jsts-roadmap",
        "subcategory": "8. Advanced Concepts",
        "tags": ["Promises", "Async/Await"],
        "difficulty": 3,
        "question_type": QuestionType.SCENARIO,
        "question_text": "You have 5 independent API calls. You use `await` on each sequentially. What is the performance problem and how do you fix it?",
        "options": {
            "A": "No problem — sequential await is always optimal.",
            "B": "Each call waits for the previous one, serialising inherently parallel work. Fix with `await Promise.all([...])` to run them concurrently.",
            "C": "The fix is to use `setTimeout` between each call.",
            "D": "Sequential await causes memory leaks in Node.js."
        },
        "correct_answer": "B",
        "explanation": "Sequential `await` means each API call waits for the last to finish, taking N × avg_latency total time. `Promise.all` fires all requests simultaneously, taking only max(latencies) — the longest single call's time.",
        "hint": "Independent work should run in parallel.",
    },

    # ── C++ Roadmap ──────────────────────────────────────────────────────────
    {
        "category_slug": "cpp-roadmap",
        "subcategory": "1. Basics First (Strong Foundation)",
        "tags": ["Pointers", "Memory"],
        "difficulty": 1,
        "question_type": QuestionType.DEFINITION,
        "question_text": "In C++, what does a pointer store?",
        "options": {
            "A": "The value of a variable.",
            "B": "The memory address of another variable.",
            "C": "A copy of a function.",
            "D": "The size of an array."
        },
        "correct_answer": "B",
        "explanation": "A pointer is a variable that holds the memory address of another variable. Dereferencing it with `*ptr` gives you the value at that address. Pointers are fundamental to C++ memory management.",
        "hint": "Pointers point to a location in memory.",
    },
    {
        "category_slug": "cpp-roadmap",
        "subcategory": "2. Master Core C++",
        "tags": ["Stack", "Heap", "Memory Management"],
        "difficulty": 2,
        "question_type": QuestionType.TRADEOFF,
        "question_text": "What is the primary difference between stack and heap allocation in C++?",
        "options": {
            "A": "Stack memory is slower; heap memory is faster.",
            "B": "Stack allocation is automatic/scoped (LIFO, fixed size); heap allocation is manual (via new/delete) with flexible, larger size.",
            "C": "Stack memory persists after a function returns; heap memory does not.",
            "D": "Heap allocation cannot be used with classes."
        },
        "correct_answer": "B",
        "explanation": "Stack memory is automatically reclaimed when a variable goes out of scope — fast and simple. Heap memory persists until explicitly freed (`delete`), enabling dynamic sizing and lifetime beyond scope, but requires careful management to avoid leaks.",
        "hint": "Stack is scoped and automatic; heap is manual.",
    },
    {
        "category_slug": "cpp-roadmap",
        "subcategory": "3. Understand DSA (Very Important Here)",
        "tags": ["Complexity", "STL"],
        "difficulty": 3,
        "question_type": QuestionType.IDENTIFICATION,
        "question_text": "What is the average time complexity of `std::unordered_map` lookup in C++?",
        "options": {"A": "O(n)", "B": "O(log n)", "C": "O(1)", "D": "O(n log n)"},
        "correct_answer": "C",
        "explanation": "`std::unordered_map` is a hash table. Under a good hash function with few collisions, lookup is O(1) on average. Worst case is O(n) due to hash collisions, but this is rare in practice.",
        "hint": "Unordered containers use hashing.",
    },
    {
        "category_slug": "cpp-roadmap",
        "subcategory": "4. Database Knowledge",
        "tags": ["RAII", "Resource Management"],
        "difficulty": 3,
        "question_type": QuestionType.DEFINITION,
        "question_text": "What does RAII (Resource Acquisition Is Initialization) mean in C++?",
        "options": {
            "A": "Resources (memory, file handles) are acquired and released manually with global functions.",
            "B": "Resources are tied to object lifetime — acquired in the constructor, released in the destructor automatically when the object goes out of scope.",
            "C": "RAII is a garbage collection mechanism like Java's GC.",
            "D": "RAII requires using raw pointers exclusively."
        },
        "correct_answer": "B",
        "explanation": "RAII binds resource management to object lifetime. When the object is destroyed (goes out of scope), the destructor automatically releases the resource. `std::unique_ptr` and `std::lock_guard` are canonical RAII types.",
        "hint": "Constructors acquire, destructors release.",
    },
    {
        "category_slug": "cpp-roadmap",
        "subcategory": "5. Systems / Performance Development",
        "tags": ["Threads", "Concurrency"],
        "difficulty": 3,
        "question_type": QuestionType.TRADEOFF,
        "question_text": "In C++, what is the primary advantage of `std::atomic<int>` over a regular `int` protected by a `std::mutex`?",
        "options": {
            "A": "Atomic types can store larger values than int.",
            "B": "Atomic operations on simple types avoid the overhead of locking/unlocking a mutex for single-instruction operations.",
            "C": "Mutexes cannot be used with integers.",
            "D": "Atomic types work only on single-core CPUs."
        },
        "correct_answer": "B",
        "explanation": "For simple read-modify-write operations on scalars, `std::atomic` uses CPU-level atomic instructions (e.g., CAS) which are far cheaper than acquiring and releasing a mutex. Use mutexes for protecting larger critical sections.",
        "hint": "Atomics are lock-free at the hardware level.",
    },
    {
        "category_slug": "cpp-roadmap",
        "subcategory": "6. Build Projects",
        "tags": ["Build Systems", "CMake"],
        "difficulty": 2,
        "question_type": QuestionType.DEFINITION,
        "question_text": "What is the main role of CMake in a C++ project?",
        "options": {
            "A": "It compiles C++ code directly into an executable.",
            "B": "It generates native build files (Makefiles, Visual Studio projects) from a platform-independent `CMakeLists.txt` description.",
            "C": "It manages third-party library downloads like pip or npm.",
            "D": "It is a debugger for C++ applications."
        },
        "correct_answer": "B",
        "explanation": "CMake is a build system generator. You write `CMakeLists.txt` once, and CMake generates the appropriate native build scripts for your platform (Make on Linux, Xcode on Mac, MSBuild on Windows).",
        "hint": "CMake generates build scripts; it doesn't compile directly.",
    },
    {
        "category_slug": "cpp-roadmap",
        "subcategory": "7. Tools & Technologies",
        "tags": ["Valgrind", "Debugging"],
        "difficulty": 3,
        "question_type": QuestionType.SCENARIO,
        "question_text": "Your C++ program crashes intermittently with corrupted data. Which tool should you use first to detect memory errors like buffer overflows and use-after-free?",
        "options": {
            "A": "gprof (CPU profiler)",
            "B": "Valgrind / AddressSanitizer",
            "C": "CMake",
            "D": "strace"
        },
        "correct_answer": "B",
        "explanation": "Valgrind (specifically `memcheck`) and AddressSanitizer (-fsanitize=address) are memory error detectors. They instrument your binary to catch out-of-bounds reads/writes, use-after-free, and memory leaks that cause intermittent crashes.",
        "hint": "Intermittent crashes in C++ strongly suggest memory corruption.",
    },
    {
        "category_slug": "cpp-roadmap",
        "subcategory": "8. Advanced Concepts",
        "tags": ["Move Semantics", "C++11"],
        "difficulty": 4,
        "question_type": QuestionType.DEFINITION,
        "question_text": "What problem does C++11 move semantics (`std::move`, rvalue references) primarily solve?",
        "options": {
            "A": "It prevents null pointer dereferences.",
            "B": "It eliminates unnecessary deep copies when transferring ownership of resources (e.g., heap memory) between objects.",
            "C": "It adds garbage collection to C++.",
            "D": "It allows functions to return multiple values."
        },
        "correct_answer": "B",
        "explanation": "Before C++11, returning a large object from a function caused an expensive copy. Move semantics allow the compiler to 'steal' the resource (heap buffer, file handle) from the source object instead of copying, leaving the source in a valid-but-empty state.",
        "hint": "Moving transfers ownership; copying duplicates data.",
    },

    # ── SQL Roadmap ──────────────────────────────────────────────────────────
    {
        "category_slug": "sql-roadmap",
        "subcategory": "1. Basics First (Strong Foundation)",
        "tags": ["SQL Basics", "Primary Key"],
        "difficulty": 1,
        "question_type": QuestionType.DEFINITION,
        "question_text": "What constraint does a PRIMARY KEY enforce on a table column in SQL?",
        "options": {
            "A": "Values must be greater than zero.",
            "B": "Values must be unique and NOT NULL — each row is uniquely identifiable.",
            "C": "Values must be foreign keys referencing another table.",
            "D": "Values are automatically encrypted."
        },
        "correct_answer": "B",
        "explanation": "A PRIMARY KEY combines UNIQUE and NOT NULL. Every row must have a distinct, non-null value in the primary key column(s), giving each row a guaranteed unique identity.",
        "hint": "It uniquely identifies each row.",
    },
    {
        "category_slug": "sql-roadmap",
        "subcategory": "2. Master Core SQL",
        "tags": ["JOINs", "Set Operations"],
        "difficulty": 2,
        "question_type": QuestionType.DEFINITION,
        "question_text": "What is the difference between INNER JOIN and LEFT JOIN?",
        "options": {
            "A": "INNER JOIN returns all rows from both tables; LEFT JOIN returns only matching rows.",
            "B": "INNER JOIN returns only rows where both tables have matching keys; LEFT JOIN returns all rows from the left table plus matched rows from the right (NULL for no match).",
            "C": "LEFT JOIN is faster than INNER JOIN.",
            "D": "They are identical when the join condition is always true."
        },
        "correct_answer": "B",
        "explanation": "INNER JOIN is the intersection — only rows with matches on both sides. LEFT JOIN keeps every row from the left table; if no match exists in the right table, the right-side columns are NULL.",
        "hint": "LEFT JOIN never drops rows from the left table.",
    },
    {
        "category_slug": "sql-roadmap",
        "subcategory": "3. Data Structures (DB Perspective)",
        "tags": ["Indexes", "B-Tree"],
        "difficulty": 2,
        "question_type": QuestionType.TRADEOFF,
        "question_text": "What is the trade-off of adding a database index to a column that is frequently used in WHERE clauses?",
        "options": {
            "A": "Indexes speed up both reads and writes equally.",
            "B": "Indexes speed up SELECT reads (avoid full table scans) but slow down INSERT/UPDATE/DELETE (index must be maintained).",
            "C": "Indexes only work on text columns.",
            "D": "Indexes increase storage but have no effect on query speed."
        },
        "correct_answer": "B",
        "explanation": "An index (typically a B-tree) stores column values in a sorted structure so the database can find rows without a full scan. But every write must also update the index, adding overhead. Index everything read-heavy; be selective on write-heavy columns.",
        "hint": "Read faster, write slower.",
    },
    {
        "category_slug": "sql-roadmap",
        "subcategory": "4. Database Systems",
        "tags": ["ACID", "Transactions"],
        "difficulty": 3,
        "question_type": QuestionType.IDENTIFICATION,
        "question_text": "In ACID transactions, what does 'Isolation' guarantee?",
        "options": {
            "A": "Data is written to disk before the transaction confirms.",
            "B": "Concurrent transactions execute as if they were serial — intermediate states are invisible to other transactions.",
            "C": "A transaction either fully completes or fully rolls back.",
            "D": "Committed data survives system crashes."
        },
        "correct_answer": "B",
        "explanation": "Isolation prevents concurrent transactions from seeing each other's partial (dirty) state. Without isolation, you'd get anomalies like dirty reads, non-repeatable reads, and phantom reads. SQL isolation levels (READ COMMITTED, SERIALIZABLE etc.) trade off isolation for performance.",
        "hint": "Isolation means transactions don't interfere with each other.",
    },
    {
        "category_slug": "sql-roadmap",
        "subcategory": "5. Data Engineering / Backend Integration",
        "tags": ["ETL", "Data Pipelines"],
        "difficulty": 3,
        "question_type": QuestionType.DEFINITION,
        "question_text": "What does ETL stand for in data engineering, and what happens in each phase?",
        "options": {
            "A": "Execute-Transform-Load: execute queries, transform results, load to cache.",
            "B": "Extract-Transform-Load: extract raw data from sources, transform/clean it, load into the target warehouse.",
            "C": "Extract-Test-Launch: a CI/CD pipeline pattern.",
            "D": "Encode-Transfer-Log: an encryption workflow."
        },
        "correct_answer": "B",
        "explanation": "ETL is the backbone of data warehousing. Extract: pull raw data from databases, APIs, files. Transform: clean, filter, join, aggregate. Load: write the processed data into an analytics store (like a data warehouse) for reporting.",
        "hint": "It's how raw operational data becomes analytics-ready.",
    },
    {
        "category_slug": "sql-roadmap",
        "subcategory": "6. Build Projects",
        "tags": ["Views", "Stored Procedures"],
        "difficulty": 2,
        "question_type": QuestionType.DEFINITION,
        "question_text": "What is a SQL VIEW and what is its main benefit?",
        "options": {
            "A": "A VIEW stores a pre-computed result set on disk for faster access.",
            "B": "A VIEW is a saved SELECT query that acts as a virtual table, simplifying complex queries and encapsulating logic.",
            "C": "A VIEW is identical to a stored procedure.",
            "D": "A VIEW locks its underlying tables from being modified."
        },
        "correct_answer": "B",
        "explanation": "A VIEW is a named SELECT statement stored in the database. Querying a view feels like querying a table, but the data is computed from the underlying tables at query time. Views simplify complex joins and provide a layer of abstraction over the schema.",
        "hint": "Views are virtual tables based on a query.",
    },
    {
        "category_slug": "sql-roadmap",
        "subcategory": "7. Tools & Technologies",
        "tags": ["Query Optimization", "EXPLAIN"],
        "difficulty": 3,
        "question_type": QuestionType.SCENARIO,
        "question_text": "A SQL query on a 10 million row table is taking 30 seconds. What is the first diagnostic step?",
        "options": {
            "A": "Add more RAM to the database server.",
            "B": "Run EXPLAIN (or EXPLAIN ANALYZE) on the query to inspect the query plan and find sequential scans.",
            "C": "Rewrite the query in a stored procedure.",
            "D": "Partition the table by date immediately."
        },
        "correct_answer": "B",
        "explanation": "`EXPLAIN` shows the query execution plan — how the database resolves the query. A sequential scan (Seq Scan) on a large table is a red flag indicating a missing index. Always diagnose before optimising.",
        "hint": "Diagnose before you optimise.",
    },
    {
        "category_slug": "sql-roadmap",
        "subcategory": "8. Advanced Concepts",
        "tags": ["Window Functions", "Analytics"],
        "difficulty": 4,
        "question_type": QuestionType.DEFINITION,
        "question_text": "What does a SQL Window Function do that a regular GROUP BY aggregate cannot?",
        "options": {
            "A": "Window functions run faster than GROUP BY.",
            "B": "Window functions compute an aggregate value across a set of related rows while still returning each individual row (no collapsing).",
            "C": "Window functions can modify data in the table.",
            "D": "GROUP BY can use window functions but not vice versa."
        },
        "correct_answer": "B",
        "explanation": "GROUP BY collapses rows into groups, losing individual row detail. Window functions (using OVER clause) compute running totals, ranks, moving averages etc. across a 'window' of rows while preserving every row in the result set.",
        "hint": "Window functions keep all rows; GROUP BY collapses them.",
    },
]


def fix():
    db = SessionLocal()
    try:
        # Step 1: Find placeholder questions — filter in Python (avoids JSON cast issues)
        all_qs = db.execute(select(Question)).scalars().all()
        placeholder_qs = [
            q for q in all_qs
            if "Incorrect foundational concept" in str(q.options)
        ]

        placeholder_ids = [q.id for q in placeholder_qs]
        print(f"Found {len(placeholder_ids)} placeholder questions to remove.")

        if placeholder_ids:
            # Delete referencing answer_attempts first
            r1 = db.execute(sql_delete(AnswerAttempt).where(AnswerAttempt.question_id.in_(placeholder_ids)))
            print(f"  Removed {r1.rowcount} answer_attempts.")

            # Delete from review_queue if referenced
            r2 = db.execute(sql_delete(ReviewQueue).where(ReviewQueue.question_id.in_(placeholder_ids)))
            print(f"  Removed {r2.rowcount} review_queue entries.")

            # Now delete the questions
            r3 = db.execute(sql_delete(Question).where(Question.id.in_(placeholder_ids)))
            print(f"Deleted {r3.rowcount} placeholder questions.")

        # Step 2: Build category slug → id map
        cats = db.execute(select(Category)).scalars().all()
        cat_map = {c.slug: c.id for c in cats}

        missing = {q["category_slug"] for q in ROADMAP_QUESTIONS} - set(cat_map)
        if missing:
            print(f"WARNING: missing categories: {missing}")

        # Step 3: Insert real questions (skip if already present)
        inserted = 0
        for q in ROADMAP_QUESTIONS:
            if q["category_slug"] not in cat_map:
                continue
            existing = db.execute(
                select(Question).where(Question.question_text == q["question_text"])
            ).scalar_one_or_none()
            if existing:
                continue
            db.add(Question(
                id=uuid.uuid4(),
                category_id=cat_map[q["category_slug"]],
                subcategory=q["subcategory"],
                tags=q.get("tags", []),
                difficulty=q["difficulty"],
                question_type=getattr(q["question_type"], "value", q["question_type"]),
                question_text=q["question_text"],
                options=q["options"],
                correct_answer=q["correct_answer"],
                explanation=q["explanation"],
                hint=q.get("hint"),
                related_concepts=q.get("related_concepts", []),
                source=getattr(QuestionSource.MANUAL, "value", QuestionSource.MANUAL),
                review_status=getattr(ReviewStatus.APPROVED, "value", ReviewStatus.APPROVED),
                times_answered=0,
                times_correct=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ))
            inserted += 1

        db.commit()
        print(f"Inserted {inserted} real questions.")
        print("Done.")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    fix()
