"""
Core evaluator module.

Evaluates submissions by applying rubric-based scoring and generating
structured feedback.
"""

from .models import Submission, EvaluationResult


class Evaluator:
    """Evaluates submissions against a set of criteria."""

    DEFAULT_CRITERIA = [
        "clarity",
        "accuracy",
        "depth",
        "structure",
        "originality",
    ]

    def __init__(self, criteria: list[str] | None = None, max_score: float = 10.0):
        self.criteria = criteria or self.DEFAULT_CRITERIA
        self.max_score = max_score

    def evaluate(self, submission: Submission) -> EvaluationResult:
        """
        Evaluate a submission and return a structured result.

        Scoring is based on heuristic checks against the submission content.
        In a production system this would call domain-specific logic or an LLM.
        """
        scores = self._score_criteria(submission)
        overall = sum(scores.values()) / len(scores) * self.max_score

        strengths = [c for c, s in scores.items() if s >= 0.7]
        weaknesses = [c for c, s in scores.items() if s < 0.5]

        feedback = self._build_feedback(overall, strengths, weaknesses)

        return EvaluationResult(
            submission_id=submission.id,
            score=round(overall, 2),
            feedback=feedback,
            strengths=strengths,
            weaknesses=weaknesses,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _score_criteria(self, submission: Submission) -> dict[str, float]:
        content = submission.content
        word_count = len(content.split())
        sentence_count = max(content.count(".") + content.count("!") + content.count("?"), 1)
        avg_sentence_len = word_count / sentence_count

        scores: dict[str, float] = {}
        for criterion in self.criteria:
            scores[criterion] = self._score_single(criterion, content, word_count, avg_sentence_len)
        return scores

    def _score_single(
        self,
        criterion: str,
        content: str,
        word_count: int,
        avg_sentence_len: float,
    ) -> float:
        """Return a normalised score [0, 1] for a single criterion."""
        if criterion == "clarity":
            # Prefer sentences of 10-25 words
            return min(1.0, max(0.0, 1 - abs(avg_sentence_len - 17.5) / 17.5))
        if criterion == "accuracy":
            # Placeholder: penalise very short submissions
            return min(1.0, word_count / 200)
        if criterion == "depth":
            return min(1.0, word_count / 400)
        if criterion == "structure":
            # Check for paragraph breaks and list markers
            has_paragraphs = "\n\n" in content or "\n" in content
            has_lists = any(marker in content for marker in ["-", "*", "1.", "•"])
            return 0.5 + 0.25 * has_paragraphs + 0.25 * has_lists
        if criterion == "originality":
            # Heuristic: longer unique-word ratio implies less boilerplate
            words = content.lower().split()
            if not words:
                return 0.0
            unique_ratio = len(set(words)) / len(words)
            return min(1.0, unique_ratio * 1.5)
        # Unknown criterion – neutral score
        return 0.5

    def _build_feedback(
        self,
        score: float,
        strengths: list[str],
        weaknesses: list[str],
    ) -> str:
        if score >= 8:
            quality = "excellent"
        elif score >= 6:
            quality = "good"
        elif score >= 4:
            quality = "adequate"
        else:
            quality = "needs significant improvement"

        parts = [f"Overall quality is {quality} (score: {score:.1f}/{self.max_score})."]
        if strengths:
            parts.append(f"Strong areas: {', '.join(strengths)}.")
        if weaknesses:
            parts.append(f"Areas to improve: {', '.join(weaknesses)}.")
        return " ".join(parts)
