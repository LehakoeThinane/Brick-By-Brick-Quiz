import pytest
from datetime import datetime, timedelta
from app.domain.adaptive_selector import weakness_weight, recency_score, difficulty_match_score, priority_score
from app.models.enums import MasteryState

def test_weakness_weight():
    assert weakness_weight(MasteryState.STRUGGLING) == 1.0
    assert weakness_weight(MasteryState.MASTERED) == 0.05
    assert weakness_weight(MasteryState.UNSEEN) == 0.5

def test_recency_score():
    now = datetime(2026, 4, 1)
    
    # Not seen yet -> 1.0
    assert recency_score(None, now) == 1.0
    
    # Seen today -> 0.0
    assert recency_score(now, now) == 0.0
    
    # Seen 7 days ago -> 0.5
    seven_days_ago = now - timedelta(days=7)
    assert recency_score(seven_days_ago, now) == 0.5
    
    # Seen 20 days ago -> 1.0 (max)
    twenty_days_ago = now - timedelta(days=20)
    assert recency_score(twenty_days_ago, now) == 1.0

def test_difficulty_match_score():
    # Exact match -> 1.0
    assert difficulty_match_score(3.0, 3) == 1.0
    
    # Far apart -> low score
    assert difficulty_match_score(1.0, 4) == 0.25
    
    # No history -> 0.5
    assert difficulty_match_score(None, 2) == 0.5

def test_priority_score_struggling_and_old():
    now = datetime(2026, 4, 1)
    last_seen = now - timedelta(days=14)
    # weakness(STRUGGLING)=1.0 * 0.5 = 0.5
    # recency(14 days)=1.0 * 0.3 = 0.3
    # difficulty(3 vs 3)=1.0 * 0.2 = 0.2
    # Total = 1.0
    score = priority_score(MasteryState.STRUGGLING, last_seen, now, 3.0, 3)
    assert score == 1.0
