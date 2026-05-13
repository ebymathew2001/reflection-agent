"""
llms/models.py
--------------
Centralised LLM model definitions for the FAQ Reflection Agent.

Two models are defined here and imported by their respective nodes:
  - generator_llm  → Google Gemini (ChatGoogleGenerativeAI) — generates FAQ answers
  - validator_llm  → Groq LLaMA (ChatGroq)                 — validates generated answers

Keeping models in one place makes swapping or upgrading models easy
without touching node logic.
"""

import os
from dotenv import load_dotenv


from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama

# Load .env variables before building any client
load_dotenv()

# ─────────────────────────────────────────────
# Node 1 — Generator LLM (Ollama)
# Used in: nodes/generator_node.py
# Role:    Produce a detailed answer to each FAQ question
# ─────────────────────────────────────────────
generator_llm = ChatOllama(
    model="qwen2.5:7b",
    temperature=0.7,
)


# ─────────────────────────────────────────────
# Node 2 — Validator LLM (Groq / LLaMA)
# Used in: nodes/validator_node.py
# Role:    Critically evaluate the generated answer for accuracy & completeness
# ─────────────────────────────────────────────
validator_llm = ChatGroq(
    model="llama-3.3-70b-versatile",    # High-quality 70B reasoning model
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.1,                    # Near-deterministic for strict validation
    max_retries=2,
)