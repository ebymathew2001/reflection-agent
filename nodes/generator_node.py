"""
nodes/generator_node.py
-----------------------
Node 1 of the reflection graph.

Responsibilities:
  - Accept the current FAQ question from state
  - Call Gemini via LangChain with structured output (GeneratedAnswer schema)
  - On retry iterations, enrich the prompt with validator's rejection reason
  - Return the generated answer and incremented iteration count back to state

This node is visited once per generate→validate cycle (up to MAX_RETRIES times
per question if the validator keeps rejecting the answer).
"""

from langchain_core.messages import HumanMessage, SystemMessage

from state import FAQAgentState, GeneratedAnswer
from llms.models import generator_llm

# Bind the Pydantic schema to the LLM so it always returns structured JSON
_generator = generator_llm.with_structured_output(GeneratedAnswer)

# System prompt stays constant — defines the LLM's persona
_SYSTEM_PROMPT = """You are a senior technical writer and AI expert.
Your job is to produce comprehensive, accurate, and well-structured answers 
to Frequently Asked Questions (FAQs) about AI, machine learning, and software engineering.

Rules for every answer:
- Minimum 60 words
- Technically accurate and up to date
- Written in clear, professional English
- No filler phrases like "Great question!"
- No markdown headers — plain paragraphs only"""


def generate_answer_node(state: FAQAgentState) -> dict:
    """
    LangGraph node: Generate an answer using Google Gemini.

    On the first attempt (iteration_count == 0) a plain prompt is sent.
    On retries, the validator's remarks are injected so the model understands
    exactly what was wrong and can improve.

    Args:
        state: Current FAQAgentState from the graph.

    Returns:
        Partial state dict with updated `current_answer` and `iteration_count`.
    """
    question: str = state["current_question"]["Question"]
    iteration: int = state["iteration_count"]
    previous_remarks: str = state.get("remarks", "")

    # ── Build the user-facing prompt ──────────────────────────────────────
    if iteration == 0:
        # First attempt — straightforward request
        user_prompt = (
            f"Please answer the following FAQ question thoroughly:\n\n"
            f"Question: {question}"
        )
    else:
        # Retry — include the validator's feedback so the model can self-correct
        user_prompt = (
            f"Your previous answer was REJECTED by the quality checker.\n"
            f"Rejection reason: {previous_remarks}\n\n"
            f"Please generate a BETTER, more complete answer to:\n"
            f"Question: {question}\n\n"
            f"Make sure the new answer directly addresses the rejection reason."
        )

    messages = [
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    print(f"  [Generator] Attempt {iteration + 1} for Q{state['current_question']['faqQuestion']}: "
          f"\"{question[:60]}...\"")

    # ── Invoke with structured output ─────────────────────────────────────
    try:
        result: GeneratedAnswer = _generator.invoke(messages)
        print(f"  [Generator] Answer generated ({len(result.answer.split())} words)")
        return {
            "current_answer": result.answer,
            "iteration_count": iteration + 1,
        }
    except Exception as e:
        print(f"  [Generator] ❌ LLM call failed: {e}")
        # Return empty answer — validator will reject it and retry/no_answer flow handles it
        return {
            "current_answer": "",
            "iteration_count": iteration + 1,
        }