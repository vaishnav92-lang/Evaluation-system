# Evaluation System

A Python application that evaluates text submissions using a rubric-based scorer and generates concise natural-language summaries powered by the **Anthropic Claude API**.

## Features

- **Rubric-based evaluation** across five criteria: clarity, accuracy, depth, structure, and originality.
- **Individual summaries** – Claude produces a 2-3 sentence summary for each evaluated submission.
- **Cohort summaries** – Claude aggregates results across a batch of submissions to give instructors a high-level overview of group performance.

## Project structure

```
Evaluation-system/
├── evaluation_system/
│   ├── __init__.py
│   ├── models.py        # Submission and EvaluationResult dataclasses
│   ├── evaluator.py     # Rubric-based evaluator
│   └── summarizer.py    # Claude-powered summarization feature
├── tests/
│   ├── test_evaluator.py
│   └── test_summarizer.py
├── main.py              # Demo entry point
├── requirements.txt
└── README.md
```

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-api-key-here"
```

## Usage

Run the demo with three sample submissions:

```bash
python main.py
```

### Programmatic usage

```python
from evaluation_system import Evaluator, Summarizer, Submission

evaluator = Evaluator()
summarizer = Summarizer()  # reads ANTHROPIC_API_KEY from environment

submission = Submission(id="s1", author="Alice", content="Your essay text here...")
result = evaluator.evaluate(submission)

# Individual summary stored on result.summary and returned as a string
summary = summarizer.summarize(result)
print(summary)

# Aggregate summary for a cohort
cohort_summary = summarizer.summarize_batch([result])
print(cohort_summary)
```

## Running tests

```bash
pip install pytest
pytest tests/
```
