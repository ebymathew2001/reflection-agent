"""
main.py
-------
Entry point for the FAQ Reflection Agent.

Execution flow:
  1. Load FAQ questions from inputs/input.json
  2. Build the LangGraph StateGraph
  3. Invoke the graph with the initial state
  4. Format and save output to outputs/output.json
  5. Print a summary to the console

Run:
    python main.py
"""

import json
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv

# Load environment variables before any LLM imports
load_dotenv()

from graph import app 


# ── Path constants ────────────────────────────────────────────────────────────
INPUT_PATH  = os.path.join("inputs",  "input.json")
OUTPUT_PATH = os.path.join("outputs", "output.json")


def load_questions(path: str) -> list:
    """
    Load FAQ questions from the input JSON file.

    Args:
        path: Relative path to the input JSON file.

    Returns:
        List of question dicts: [{"faqQuestion": int, "Question": str}, ...]

    Raises:
        SystemExit: If the file is missing or malformed.
    """
    if not os.path.exists(path):
        print(f"[ERROR] Input file not found: {path}")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"[ERROR] Invalid JSON in {path}: {e}")
            sys.exit(1)

    if not isinstance(data, list) or len(data) == 0:
        print("[ERROR] input.json must be a non-empty JSON array.")
        sys.exit(1)

    print(f"[Init] Loaded {len(data)} question(s) from {path}")
    return data


def save_output(output: dict, path: str) -> None:
    """
    Save the final structured output to a JSON file.

    Args:
        output: The final output dict to serialise.
        path:   Relative path to the output JSON file.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"[Output] Results saved → {path}")


def print_summary(results: list) -> None:
    """Print a console summary table of all processed questions."""
    answered  = sum(1 for r in results if r["status"] == "answered")
    no_answer = sum(1 for r in results if r["status"] == "no_answer")

    print("\n" + "─" * 60)
    print(f"  SUMMARY")
    print("─" * 60)
    print(f"  Total Questions : {len(results)}")
    print(f"  Answered        : {answered}")
    print(f"  No Answer       : {no_answer}")
    print("─" * 60)

    for r in results:
        status_icon = "✅" if r["status"] == "answered" else "❌"
        print(
            f"  Q{r['faqQuestion']:>2}. {status_icon}  "
            f"[{r['iterationCount']} iter]  "
            f"{r['Question'][:45]}..."
        )
    print("─" * 60 + "\n")


def main() -> None:
    """Main execution function."""
    print("\n" + "=" * 60)
    print("  FAQ Reflection Agent  |  LangGraph + Ollama + Groq")
    print("=" * 60 + "\n")

    # ── Step 1: Load questions ────────────────────────────────────────────
    questions = load_questions(INPUT_PATH)

    # ── Step 2: Build the compiled graph ──────────────────────────────────
    print("[Init] Building LangGraph StateGraph...")
    
    print("[Init] Graph compiled successfully.\n")

    # ── Step 3: Define initial state ──────────────────────────────────────
    initial_state = {
        "questions":        questions,
        "current_index":    0,
        "current_question": {},
        "current_answer":   "",
        "is_valid":         False,
        "remarks":          "",
        "iteration_count":  0,
        "results":          [],
    }

    # ── Step 4: Run the graph ─────────────────────────────────────────────
    # ── Step 4: Run the graph ─────────────────────────────────────────────
    print("[Run] Starting agent graph execution...\n")
    start_time = datetime.now(timezone.utc)

    try:
        final_state: dict = app.invoke(initial_state)
    except Exception as e:
        print(f"\n[FATAL] Graph execution failed: {e}")
        sys.exit(1)

    end_time = datetime.now(timezone.utc)
    elapsed  = (end_time - start_time).total_seconds()
    print(f"\n[Run] Graph execution finished in {elapsed:.1f}s")
    # ── Step 5: Format and save output ────────────────────────────────────
    output = {
        "totalQuestions": len(questions),
        "processedAt":    start_time.isoformat().replace("+00:00", "Z"),
        "durationSeconds": round(elapsed, 2),
        "results":        final_state["results"],
    }

    save_output(output, OUTPUT_PATH)

    # ── Step 6: Console summary ───────────────────────────────────────────
    print_summary(final_state["results"])


if __name__ == "__main__":
    main()