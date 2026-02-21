from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Submission:
    id: str
    author: str
    content: str
    topic: Optional[str] = None


@dataclass
class EvaluationResult:
    submission_id: str
    score: float
    feedback: str
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    summary: Optional[str] = None

    def __str__(self) -> str:
        lines = [
            f"Submission ID : {self.submission_id}",
            f"Score         : {self.score:.1f}/10",
            f"Feedback      : {self.feedback}",
        ]
        if self.strengths:
            lines.append("Strengths     : " + "; ".join(self.strengths))
        if self.weaknesses:
            lines.append("Weaknesses    : " + "; ".join(self.weaknesses))
        if self.summary:
            lines.append(f"Summary       : {self.summary}")
        return "\n".join(lines)
