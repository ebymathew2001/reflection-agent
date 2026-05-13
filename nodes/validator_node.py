"""
nodes/validator_node.py
-----------------------
Node 2 of the reflection graph.

Responsibilities:
  - Accept the current question + Gemini's generated answer from state
  - Call Groq LLaMA with structured output (ValidationOutput schema)
  - Apply a strict validation rubric (accuracy, completeness, length, clarity)
  - Return is_valid (bool) and remarks (str) back to state

The conditional edge after this node reads `is_valid` to decide whether to
accept the answer, retry generation, or mark the question as no_answer.
"""

from langchain_core.messages import HumanMessage, SystemMessage

from state import FAQAgentState, ValidationOutput
from llms.models import validator_llm

# Bind the Pydantic schema — forces Groq to respond with {is_valid, remarks}
_validator = validator_llm.with_structured_output(ValidationOutput)

# Strict validation rubric injected as system context
_SYSTEM_PROMPT = """You are a strict but fair QA reviewer for an AI-powered FAQ system.
Your job is to evaluate whether a given answer meets quality standards.

Validation rubric — ALL criteria must pass for is_valid = true:
  1. ACCURACY    → The answer is technically correct and not misleading
  2. COMPLETENESS → The question is fully answered, not just partially
  3. LENGTH      → The answer is at least 50 words long
  4. CLARITY     → The answer is easy to understand for a developer audience
  5. RELEVANCE   → The answer actually addresses the specific question asked

If ANY criterion fails, set is_valid = false and clearly state which criterion
failed and what specific improvement is needed in your remarks.

Do not pass vague or generic answers. Be strict."""


def validate_answer_node(state: FAQAgentState) -> dict:
    """
    LangGraph node: Validate the generated answer using Groq LLaMA.

    Reads current_question and current_answer from state, sends them to
    the validator LLM, and writes back is_valid + remarks.

    Args:
        state: Current FAQAgentState from the graph.

    Returns:
        Partial state dict with updated `is_valid` and `remarks`.
    """
    question: str = state["current_question"]["Question"]
    answer: str = state["current_answer"]
    iteration: int = state["iteration_count"]

    # ── Guard: skip LLM call if generator already failed ─────────────────
    if not answer.strip():
        print(f"  [Validator] ⚠️  Empty answer received — marking invalid")
        return {
            "is_valid": False,
            "remarks": "Generator returned an empty answer.",
        }

    user_prompt = (
        f"Evaluate the following FAQ answer against all rubric criteria:\n\n"
        f"Question: {question}\n\n"
        f"Answer: {answer}\n\n"
        f"Return your structured verdict."
    )

    messages = [
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    print(f"  [Validator] Checking answer (iteration {iteration})...")

    # ── Invoke Groq with structured output ────────────────────────────────
    try:
        result: ValidationOutput = _validator.invoke(messages)
        verdict = "✅ VALID" if result.is_valid else "❌ INVALID"
        print(f"  [Validator] Verdict: {verdict} — {result.remarks[:80]}...")
        return {
            "is_valid": result.is_valid,
            "remarks": result.remarks,
        }
    except Exception as e:
        print(f"  [Validator] ❌ LLM call failed: {e}")
        # Treat as invalid — retry/no_answer flow handles the rest
        return {
            "is_valid": False,
            "remarks": f"Validator encountered an error: {str(e)}",
        }