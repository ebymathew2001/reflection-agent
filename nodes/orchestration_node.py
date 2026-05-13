from state import FAQAgentState

MAX_RETRIES = 3

def load_question_node(state: FAQAgentState) -> dict:
    idx = state["current_index"]
    current_q = state["questions"][idx]
    print(f"\n{'='*60}")
    print(f"Processing Q{current_q['faqQuestion']}: {current_q['Question'][:70]}")
    print(f"{'='*60}")
    return {
        "current_question": current_q,
        "current_answer": "",
        "is_valid": False,
        "remarks": "",
        "iteration_count": 0,
    }

def save_result_node(state: FAQAgentState) -> dict:
    results = list(state.get("results", []))
    is_valid = state["is_valid"]
    iteration_count = state["iteration_count"]
    faq_id = state["current_question"]["faqQuestion"]

    if is_valid:
        result = {
            "faqQuestion": faq_id,
            "Question": state["current_question"]["Question"],
            "iterationCount": iteration_count,
            "status": "answered",
            "Answer": state["current_answer"],
            "checkedAnswer": True,
            "remarks": state["remarks"],
        }
        print(f"  [Save] Q{faq_id} → ANSWERED after {iteration_count} iteration(s)")
    else:
        result = {
            "faqQuestion": faq_id,
            "Question": state["current_question"]["Question"],
            "iterationCount": iteration_count,
            "status": "no_answer",
            "Answer": "-",
            "checkedAnswer": False,
            "remarks": state["remarks"] or f"Max retries ({MAX_RETRIES}) reached.",
        }
        print(f"  [Save] Q{faq_id} → NO_ANSWER after {iteration_count} iteration(s)")

    results.append(result)
    return {
        "results": results,
        "current_index": state["current_index"] + 1,
    }