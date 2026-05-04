"""
Shuffles the A/B/C/D options for every question in the DB so correct answers
are distributed evenly. Correct answer key is updated to follow the moved value.
Safe to re-run — it re-shuffles each time.
"""
import sys, random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.question import Question


def shuffle_question(options: dict, correct_answer: str):
    """Shuffle option values, keep A/B/C/D keys, return (new_options, new_correct_key)."""
    keys = list(options.keys())          # e.g. ['A','B','C','D']
    values = [options[k] for k in keys]  # original values in order
    correct_value = options[correct_answer]

    random.shuffle(values)

    new_options = {keys[i]: values[i] for i in range(len(keys))}
    new_correct = next(k for k, v in new_options.items() if v == correct_value)
    return new_options, new_correct


def main():
    random.seed()  # true random each run
    db = SessionLocal()
    try:
        questions = db.execute(select(Question)).scalars().all()
        updated = 0
        for q in questions:
            if not isinstance(q.options, dict) or not q.correct_answer:
                continue
            new_opts, new_correct = shuffle_question(q.options, q.correct_answer)
            # Only write back if something actually changed
            if new_correct != q.correct_answer or new_opts != q.options:
                q.options = new_opts
                q.correct_answer = new_correct
                updated += 1

        db.commit()

        # Verify distribution
        all_qs = db.execute(select(Question)).scalars().all()
        dist: dict[str, int] = {}
        for q in all_qs:
            k = q.correct_answer or "?"
            dist[k] = dist.get(k, 0) + 1

        print(f"Updated {updated} questions.")
        print("Correct-answer distribution:", dict(sorted(dist.items())))
    finally:
        db.close()


if __name__ == "__main__":
    main()
