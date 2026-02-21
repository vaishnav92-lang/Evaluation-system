"""
Summarization feature.

Uses the Anthropic Claude API to produce concise natural-language summaries
of individual EvaluationResult objects or batches of results.
"""

from __future__ import annotations

import os

import anthropic

from .models import EvaluationResult


class Summarizer:
    """
    Generates summaries of evaluation results using Claude.

    Parameters
    ----------
    api_key:
        Anthropic API key.  Falls back to the ``ANTHROPIC_API_KEY``
        environment variable when not provided.
    model:
        Claude model to use for summarization.
    max_tokens:
        Maximum tokens in the generated summary.
    """

    DEFAULT_MODEL = "claude-opus-4-6"

    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        max_tokens: int = 512,
    ) -> None:
        self._client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        self.model = model
        self.max_tokens = max_tokens

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def summarize(self, result: EvaluationResult) -> str:
        """
        Generate a concise summary for a single evaluation result.

        The summary is also stored in ``result.summary`` in-place so the
        result object carries the enriched data going forward.

        Parameters
        ----------
        result:
            An EvaluationResult produced by :class:`Evaluator`.

        Returns
        -------
        str
            A short, human-readable summary of the evaluation.
        """
        prompt = self._build_single_prompt(result)
        summary = self._call_claude(prompt)
        result.summary = summary
        return summary

    def summarize_batch(self, results: list[EvaluationResult]) -> str:
        """
        Generate an aggregate summary across multiple evaluation results.

        Useful for giving instructors or reviewers a high-level picture of
        how an entire cohort performed.

        Parameters
        ----------
        results:
            A list of EvaluationResult objects to summarise together.

        Returns
        -------
        str
            A cohort-level summary covering trends, score distribution, and
            common strengths / weaknesses.
        """
        if not results:
            return "No evaluation results to summarise."
        prompt = self._build_batch_prompt(results)
        return self._call_claude(prompt)

    # ------------------------------------------------------------------
    # Prompt builders
    # ------------------------------------------------------------------

    @staticmethod
    def _build_single_prompt(result: EvaluationResult) -> str:
        strengths_text = ", ".join(result.strengths) if result.strengths else "none identified"
        weaknesses_text = ", ".join(result.weaknesses) if result.weaknesses else "none identified"
        return (
            "You are an educational evaluator assistant. "
            "Summarise the following evaluation result in 2-3 concise sentences "
            "suitable for the submitter to read. "
            "Focus on the most important takeaway and one actionable improvement tip.\n\n"
            f"Submission ID : {result.submission_id}\n"
            f"Score         : {result.score}/10\n"
            f"Feedback      : {result.feedback}\n"
            f"Strengths     : {strengths_text}\n"
            f"Weaknesses    : {weaknesses_text}\n"
        )

    @staticmethod
    def _build_batch_prompt(results: list[EvaluationResult]) -> str:
        n = len(results)
        avg_score = sum(r.score for r in results) / n
        all_strengths: list[str] = []
        all_weaknesses: list[str] = []
        for r in results:
            all_strengths.extend(r.strengths)
            all_weaknesses.extend(r.weaknesses)

        def most_common(items: list[str], top: int = 3) -> list[str]:
            from collections import Counter
            return [item for item, _ in Counter(items).most_common(top)]

        top_strengths = most_common(all_strengths)
        top_weaknesses = most_common(all_weaknesses)

        score_lines = "\n".join(
            f"  - {r.submission_id}: {r.score}/10" for r in results
        )

        return (
            "You are an educational evaluator assistant. "
            "Summarise the evaluation results for the following cohort in 3-4 concise sentences. "
            "Highlight the overall performance level, the most common strengths, "
            "the most common weaknesses, and one group-level recommendation.\n\n"
            f"Number of submissions : {n}\n"
            f"Average score         : {avg_score:.2f}/10\n"
            f"Top strengths         : {', '.join(top_strengths) or 'none identified'}\n"
            f"Top weaknesses        : {', '.join(top_weaknesses) or 'none identified'}\n"
            f"Individual scores     :\n{score_lines}\n"
        )

    # ------------------------------------------------------------------
    # Claude API call
    # ------------------------------------------------------------------

    def _call_claude(self, prompt: str) -> str:
        message = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()
