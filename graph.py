from langgraph.graph import StateGraph, END
from state import FAQAgentState

from nodes.generator_node     import generate_answer_node
from nodes.validator_node     import validate_answer_node
from nodes.orchestration_node import load_question_node, save_result_node
from routing                  import route_after_validation, route_after_save

workflow = StateGraph(FAQAgentState)

# ── Add nodes ──
workflow.add_node("load_faq_question",   load_question_node)
workflow.add_node("generate_faq_answer", generate_answer_node)
workflow.add_node("validate_faq_answer", validate_answer_node)
workflow.add_node("save_faq_result",     save_result_node)

# ── Entry point ──
workflow.set_entry_point("load_faq_question")

# ── Static edges ──
workflow.add_edge("load_faq_question",   "generate_faq_answer")
workflow.add_edge("generate_faq_answer", "validate_faq_answer")

# 
workflow.add_conditional_edges(
    "validate_faq_answer",
    route_after_validation,
    {"generate_faq_answer": "generate_faq_answer", "save_faq_result": "save_faq_result"}
)

workflow.add_conditional_edges(
    "save_faq_result",
    route_after_save,
    {"load_faq_question": "load_faq_question", END: END}
)

app = workflow.compile()

if __name__ == "__main__":
    png_image = app.get_graph().draw_mermaid_png()
    with open("faq_agent_graph.png", "wb") as f:
        f.write(png_image)
    print("Graph saved → faq_agent_graph.png")