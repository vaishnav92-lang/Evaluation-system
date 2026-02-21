"""
Evaluation-system entry point.

Demonstrates evaluating a batch of submissions and generating summaries
with the Claude-powered Summarizer.

Usage:
    ANTHROPIC_API_KEY=<key> python main.py
"""

from evaluation_system import Evaluator, Summarizer, Submission


SAMPLE_SUBMISSIONS = [
    Submission(
        id="sub-001",
        author="Alice",
        topic="Climate Change",
        content=(
            "Climate change is one of the most pressing issues of our time. "
            "Rising global temperatures, driven primarily by greenhouse gas emissions, "
            "are causing widespread environmental disruption.\n\n"
            "The effects include melting ice caps, rising sea levels, and increasingly "
            "severe weather events. These changes threaten ecosystems, agriculture, "
            "and human settlements worldwide.\n\n"
            "Addressing climate change requires urgent, coordinated global action—"
            "including transitioning to renewable energy, improving energy efficiency, "
            "and protecting natural carbon sinks such as forests."
        ),
    ),
    Submission(
        id="sub-002",
        author="Bob",
        topic="Climate Change",
        content="Climate is changing. It is bad. We need to fix it.",
    ),
    Submission(
        id="sub-003",
        author="Carol",
        topic="Climate Change",
        content=(
            "Global warming refers to the long-term heating of Earth's surface "
            "observed since the pre-industrial period due to human activities, "
            "primarily fossil fuel burning, which increases heat-trapping greenhouse "
            "gas levels in Earth's atmosphere.\n\n"
            "- Deforestation accelerates CO₂ accumulation.\n"
            "- Methane from livestock is a potent short-lived climate pollutant.\n"
            "- Ocean acidification threatens marine biodiversity.\n\n"
            "Policy interventions such as carbon pricing and international agreements "
            "like the Paris Accord are critical mechanisms for coordinating mitigation "
            "efforts across nations."
        ),
    ),
]


def main() -> None:
    evaluator = Evaluator()
    summarizer = Summarizer()

    results = []
    for submission in SAMPLE_SUBMISSIONS:
        result = evaluator.evaluate(submission)
        results.append(result)

        print(f"\n{'=' * 60}")
        print(f"Evaluating: {submission.author} ({submission.id})")
        print("=" * 60)
        print(result)

        print("\n-- Individual Summary (via Claude) --")
        summary = summarizer.summarize(result)
        print(summary)

    print(f"\n{'=' * 60}")
    print("Cohort Summary (via Claude)")
    print("=" * 60)
    cohort_summary = summarizer.summarize_batch(results)
    print(cohort_summary)


if __name__ == "__main__":
    main()
