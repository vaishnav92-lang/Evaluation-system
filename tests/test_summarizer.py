"""Tests for the Summarizer module."""

from unittest.mock import MagicMock, patch

import pytest

from evaluation_system.models import EvaluationResult
from evaluation_system.summarizer import Summarizer


def _make_result(submission_id="s1", score=7.5, strengths=None, weaknesses=None):
    return EvaluationResult(
        submission_id=submission_id,
        score=score,
        feedback="Overall quality is good.",
        strengths=strengths or ["clarity", "structure"],
        weaknesses=weaknesses or ["depth"],
    )


def _mock_summarizer() -> Summarizer:
    """Return a Summarizer whose underlying Anthropic client is mocked."""
    with patch("evaluation_system.summarizer.anthropic.Anthropic"):
        s = Summarizer(api_key="test-key")
    # Replace client with a fresh mock so individual tests can configure it
    s._client = MagicMock()
    return s


class TestSummarizer:
    def test_summarize_returns_string(self):
        summarizer = _mock_summarizer()
        fake_text = "This is a mock summary."
        summarizer._client.messages.create.return_value = MagicMock(
            content=[MagicMock(text=fake_text)]
        )
        result = _make_result()
        summary = summarizer.summarize(result)
        assert isinstance(summary, str)
        assert summary == fake_text

    def test_summarize_stores_on_result(self):
        summarizer = _mock_summarizer()
        summarizer._client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="Stored summary.")]
        )
        result = _make_result()
        summarizer.summarize(result)
        assert result.summary == "Stored summary."

    def test_summarize_calls_api_once(self):
        summarizer = _mock_summarizer()
        summarizer._client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="ok")]
        )
        result = _make_result()
        summarizer.summarize(result)
        assert summarizer._client.messages.create.call_count == 1

    def test_summarize_batch_empty(self):
        summarizer = _mock_summarizer()
        out = summarizer.summarize_batch([])
        assert "No evaluation results" in out
        summarizer._client.messages.create.assert_not_called()

    def test_summarize_batch_returns_string(self):
        summarizer = _mock_summarizer()
        summarizer._client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="Batch summary here.")]
        )
        results = [_make_result("s1", 8.0), _make_result("s2", 5.5)]
        out = summarizer.summarize_batch(results)
        assert isinstance(out, str)
        assert out == "Batch summary here."

    def test_summarize_batch_calls_api_once(self):
        summarizer = _mock_summarizer()
        summarizer._client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="ok")]
        )
        results = [_make_result("s1"), _make_result("s2"), _make_result("s3")]
        summarizer.summarize_batch(results)
        assert summarizer._client.messages.create.call_count == 1

    def test_build_single_prompt_contains_score(self):
        result = _make_result(score=6.0)
        prompt = Summarizer._build_single_prompt(result)
        assert "6.0" in prompt

    def test_build_batch_prompt_contains_average(self):
        results = [_make_result("a", 8.0), _make_result("b", 6.0)]
        prompt = Summarizer._build_batch_prompt(results)
        assert "7.00" in prompt

    def test_model_passed_to_api(self):
        summarizer = _mock_summarizer()
        summarizer.model = "claude-test-model"
        summarizer._client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="ok")]
        )
        summarizer.summarize(_make_result())
        call_kwargs = summarizer._client.messages.create.call_args[1]
        assert call_kwargs["model"] == "claude-test-model"
