from langgraph.graph import END
from state import FAQAgentState

MAX_RETRIES = 3

def route_after_validation(state: FAQAgentState) -> str:
    if state["is_valid"]:
        return "save_result"
    if state["iteration_count"] >= MAX_RETRIES:
        print(f"  [Router] Max retries reached → no_answer")
        return "save_result"
    remaining = MAX_RETRIES - state["iteration_count"]
    print(f"  [Router] Invalid → retrying ({remaining} left)")
    return "generate_answer"

def route_after_save(state: FAQAgentState) -> str:
    if state["current_index"] < len(state["questions"]):
        return "load_question"
    print("All questions processed.")
    return END