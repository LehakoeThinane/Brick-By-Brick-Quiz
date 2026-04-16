import pytest
from app.domain.answer_evaluator import evaluate_answer
from app.models.enums import MasterySignal

def test_evaluate_answer_correct_fast():
    # Correct answer under 20s -> STRONG
    result = evaluate_answer("A", "A", 15_000)
    assert result.is_correct is True
    assert result.mastery_signal == MasterySignal.STRONG

def test_evaluate_answer_correct_medium():
    # Correct answer between 20-45s -> PARTIAL
    result = evaluate_answer("B", "b", 30_000)
    assert result.is_correct is True
    assert result.mastery_signal == MasterySignal.PARTIAL

def test_evaluate_answer_correct_slow():
    # Correct answer > 45s -> WEAK
    result = evaluate_answer("C", "C", 50_000)
    assert result.is_correct is True
    assert result.mastery_signal == MasterySignal.WEAK

def test_evaluate_answer_incorrect():
    # Incorrect answer -> MISS regardless of time
    result = evaluate_answer("A", "C", 10_000)
    assert result.is_correct is False
    assert result.mastery_signal == MasterySignal.MISS

def test_evaluate_answer_whitespace_and_case():
    result = evaluate_answer("  D  ", "d", 15_000)
    assert result.is_correct is True
    assert result.mastery_signal == MasterySignal.STRONG
