# FAQ Reflection Agent

An AI-powered agent that automatically answers FAQ questions using a **reflection loop** — a generator LLM produces answers, a validator LLM critiques them, and the generator retries until the answer meets quality standards or the retry limit is reached.

Built with **LangGraph**, **Ollama (qwen2.5:7b)**, and **Groq (llama-3.3-70b-versatile)**.

---

## How It Works

```
input.json → load question → generate answer → validate answer → save result → output.json
                                 ↑                    |
                                 └────── retry ───────┘
                                      (if invalid, max 3 retries)
```

1. Questions are loaded from `inputs/input.json`
2. For each question, the **generator LLM** (qwen2.5:7b via Ollama) produces an answer
3. The **validator LLM** (llama-3.3-70b via Groq) checks the answer against a strict rubric
4. If the answer fails, the rejection reason is fed back to the generator for a better attempt
5. After 3 failed attempts, the question is marked as `no_answer`
6. Final results are saved to `outputs/output.json`

---

## Project Structure

```
reflection-agent/
├── inputs/
│   └── input.json              # FAQ questions to process
├── outputs/
│   └── output.json             # Generated answers (auto-created)
├── llms/
│   └── models.py               # LLM client definitions (Ollama + Groq)
├── nodes/
│   ├── generator_node.py       # Node 1: generates answers
│   ├── validator_node.py       # Node 2: validates answers
│   └── orchestration_node.py   # load_question and save_result nodes
├── graph.py                    # LangGraph StateGraph wiring
├── routing.py                  # Conditional edge routing functions
├── state.py                    # Shared state + Pydantic output schemas
├── main.py                     # Entry point
├── requirements.txt
└── .env                        # API keys (not committed)
```

---

## Requirements

- Python 3.10+
- [Ollama](https://ollama.com) installed and running locally
- A [Groq](https://console.groq.com) API key

### Ollama model

Pull the generator model before running:

```bash
ollama pull qwen2.5:7b
```

---

## Setup

**1. Clone the repository**

```bash
git clone <repo-url>
cd reflection-agent
```

**2. Create and activate a virtual environment**

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Create a `.env` file**

```
GROQ_API_KEY=your_groq_api_key_here
```

Get your free Groq API key at [console.groq.com](https://console.groq.com).

**5. Add your questions to `inputs/input.json`**

```json
[
  { "faqQuestion": 1, "Question": "What is LangGraph?" },
  { "faqQuestion": 2, "Question": "What is a RAG pipeline?" }
]
```

**6. Run the agent**

```bash
python main.py
```

---

## Output

Results are saved to `outputs/output.json`:

```json
{
  "totalQuestions": 2,
  "processedAt": "2026-05-12T18:10:18Z",
  "durationSeconds": 174.88,
  "results": [
    {
      "faqQuestion": 1,
      "Question": "What is LangGraph?",
      "iterationCount": 1,
      "status": "answered",
      "Answer": "LangGraph is a framework...",
      "checkedAnswer": true,
      "remarks": "Answer is accurate and complete."
    }
  ]
}
```

Each result has a `status` of either `answered` or `no_answer`.

---

## Models

| Role      | Model                    | Provider | Purpose                        |
|-----------|--------------------------|----------|--------------------------------|
| Generator | `qwen2.5:7b`             | Ollama   | Produces answers (local)       |
| Validator | `llama-3.3-70b-versatile`| Groq     | Validates answer quality       |

### Validation Rubric

The validator checks every answer against five criteria — all must pass:

1. **Accuracy** — technically correct and not misleading
2. **Completeness** — question is fully answered
3. **Length** — at least 50 words
4. **Clarity** — easy to understand for a developer audience
5. **Relevance** — directly addresses the specific question asked

---

## Configuration

| Setting       | Location                  | Default | Description                        |
|---------------|---------------------------|---------|------------------------------------|
| `MAX_RETRIES` | `routing.py`, `orchestration_node.py` | `3` | Max generate→validate cycles per question |
| `temperature` | `llms/models.py`          | `0.7` (generator), `0.1` (validator) | LLM creativity level |

---

## Console Output

```
============================================================
  FAQ Reflection Agent  |  LangGraph + Ollama + Groq
============================================================

[Init] Loaded 5 question(s) from inputs\input.json
[Init] Graph compiled successfully.

============================================================
Processing Q1: What is LangGraph and how does it differ from LangChain?
============================================================
  [Generator] Attempt 1 for Q1: "What is LangGraph..."
  [Generator] Answer generated (308 words)
  [Validator] Checking answer (iteration 1)...
  [Validator] Verdict: ✅ VALID — The answer is accurate and complete...
  [Save] Q1 → ANSWERED after 1 iteration(s)

────────────────────────────────────────────────────────────
  SUMMARY
────────────────────────────────────────────────────────────
  Total Questions : 5
  Answered        : 5
  No Answer       : 0
────────────────────────────────────────────────────────────
  Q 1. ✅  [1 iter]  What is LangGraph and how does it differ...
  Q 2. ✅  [1 iter]  What is a RAG pipeline and when should...
────────────────────────────────────────────────────────────
```

---

## Dependencies

```
python-dotenv==1.2.2
pydantic==2.13.4
langchain==1.2.18
langchain-core==1.4.0
langchain-groq==1.1.2
langchain-ollama==1.1.0
langgraph==1.1.10
```

---

## Error Handling

The agent handles failures gracefully without crashing the full run:

- If the **generator LLM** fails, an empty answer is returned and the validator marks it invalid, triggering the retry flow
- If the **validator LLM** fails, the answer is treated as invalid and retried
- If **max retries** are reached, the question is saved as `no_answer` and processing continues with the next question
- If the **graph itself** crashes unexpectedly, a clean fatal error message is shown instead of a raw traceback