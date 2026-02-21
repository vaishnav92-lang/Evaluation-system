"""Tests for the Evaluator module."""

import pytest
from evaluation_system.evaluator import Evaluator
from evaluation_system.models import Submission, EvaluationResult


@pytest.fixture
def evaluator():
    return Evaluator()


@pytest.fixture
def short_submission():
    return Submission(id="s1", author="Test", content="Short text.")


@pytest.fixture
def rich_submission():
    return Submission(
        id="s2",
        author="Test",
        content=(
            "This is a well-structured essay with multiple paragraphs.\n\n"
            "The second paragraph adds depth and detail to the argument.\n\n"
            "- Supporting point one\n"
            "- Supporting point two\n\n"
            "The conclusion ties everything together in a coherent manner, "
            "demonstrating a solid understanding of the topic at hand."
        ),
    )


class TestEvaluator:
    def test_evaluate_returns_result(self, evaluator, short_submission):
        result = evaluator.evaluate(short_submission)
        assert isinstance(result, EvaluationResult)

    def test_submission_id_preserved(self, evaluator, short_submission):
        result = evaluator.evaluate(short_submission)
        assert result.submission_id == short_submission.id

    def test_score_in_range(self, evaluator, rich_submission):
        result = evaluator.evaluate(rich_submission)
        assert 0 <= result.score <= 10

    def test_rich_submission_scores_higher(self, evaluator, short_submission, rich_submission):
        short_result = evaluator.evaluate(short_submission)
        rich_result = evaluator.evaluate(rich_submission)
        assert rich_result.score > short_result.score

    def test_feedback_is_string(self, evaluator, short_submission):
        result = evaluator.evaluate(short_submission)
        assert isinstance(result.feedback, str)
        assert len(result.feedback) > 0

    def test_strengths_and_weaknesses_are_lists(self, evaluator, short_submission):
        result = evaluator.evaluate(short_submission)
        assert isinstance(result.strengths, list)
        assert isinstance(result.weaknesses, list)

    def test_custom_criteria(self):
        ev = Evaluator(criteria=["clarity", "depth"])
        sub = Submission(id="s3", author="Test", content="Some content here.")
        result = ev.evaluate(sub)
        assert isinstance(result, EvaluationResult)

    def test_str_representation(self, evaluator, rich_submission):
        result = evaluator.evaluate(rich_submission)
        s = str(result)
        assert "Score" in s
        assert "Feedback" in s

    def test_empty_content_does_not_crash(self, evaluator):
        sub = Submission(id="s4", author="Test", content="")
        result = evaluator.evaluate(sub)
        assert result.score >= 0

    def test_summary_initially_none(self, evaluator, short_submission):
        result = evaluator.evaluate(short_submission)
        assert result.summary is None
