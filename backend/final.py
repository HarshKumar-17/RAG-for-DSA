from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from openai import OpenAI
import chromadb
import json
import re
import os
from datetime import datetime

# Load environment variables
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))
load_dotenv()

# -----------------------------
# Vector DB connection (native chromadb — no torch needed)
# -----------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
persistent_directory = os.path.join(BASE_DIR, "db", "chroma_db")

# ChromaDB's default embedding function is ONNXMiniLM_L6_V2
# — same all-MiniLM-L6-v2 model used during ingestion, but runs
#   on onnxruntime (~60 MB) instead of torch (~2 GB)
chroma_client = chromadb.PersistentClient(path=persistent_directory)
collection = chroma_client.get_or_create_collection(name="langchain")

# -----------------------------
# LLM Client (Groq Free Tier with OpenAI fallback)
# -----------------------------

_client = None
_model_name = "qwen/qwen3.8-27b"

def get_llm_client():
    global _client, _model_name
    if _client is None:
        groq_api_key = os.getenv("GROQ_API_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")

        if groq_api_key:
            _client = OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=groq_api_key
            )
            # Default to qwen/qwen3.8-27b or openai/gpt-oss-120b on Groq
            _model_name = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
        elif openai_api_key:
            _client = OpenAI(api_key=openai_api_key)
            _model_name = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        else:
            raise ValueError(
                "Neither GROQ_API_KEY nor OPENAI_API_KEY is set. "
                "Get a free API key at https://console.groq.com and set GROQ_API_KEY in Render/environment."
            )
    return _client, _model_name

def generate_text(prompt):
    client, model = get_llm_client()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0.3
    )
    return response.choices[0].message.content

# -----------------------------
# Chat memory
# -----------------------------

chat_history = []

# -----------------------------
# Answer validation
# -----------------------------

def validate_and_format_answer(answer):

    validation_report = []

    if "```" in answer:
        validation_report.append("Code block detected.")
    else:
        validation_report.append("No formatted code block found.")

    complexity_pattern = r"O\([^)]+\)"
    complexities = re.findall(complexity_pattern, answer)

    if complexities:
        validation_report.append(f"Time complexity mentioned: {', '.join(complexities)}")
    else:
        validation_report.append("No time complexity mentioned.")

    formatted_answer = answer.strip()

    return formatted_answer, validation_report


# -----------------------------
# Logging interactions
# -----------------------------

LOG_FILE = os.path.join(BASE_DIR, "rag_logs.json")

def log_interaction(question, search_question, sources, answer, validation):

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "user_question": question,
        "search_query": search_question,
        "retrieved_sources": sources,
        "answer": answer,
        "validation": validation
    }

    try:
        with open(LOG_FILE, "r") as f:
            data = json.load(f)
    except:
        data = []

    data.append(log_entry)

    with open(LOG_FILE, "w") as f:
        json.dump(data, f, indent=4)


# -----------------------------
# Analytics
# -----------------------------

def show_analytics():

    try:
        with open(LOG_FILE, "r") as f:
            data = json.load(f)
    except:
        print("No logs available yet.")
        return

    print("\n--- Analytics ---")
    print("Total Queries:", len(data))

    sources = {}

    for entry in data:
        for src in entry["retrieved_sources"]:
            sources[src] = sources.get(src, 0) + 1

    print("\nMost Retrieved Sources:")

    for k, v in sources.items():
        print(k, ":", v)


# -----------------------------
# Main RAG logic
# -----------------------------

def ask_question(user_question):

    print(f"\n--- You asked: {user_question} ---")

    # Rewrite question using chat history
    if chat_history:

        history_text = "\n".join(
            [msg.content for msg in chat_history]
        )

        rewrite_prompt = f"""
Rewrite the user question so it can be used for document search.

Chat history:
{history_text}

User question:
{user_question}

Rewritten query:
"""

        response_text = generate_text(rewrite_prompt)
        search_question = response_text.strip()

        print(f"Searching for: {search_question}")

    else:
        search_question = user_question

    # Retrieve documents using chromadb directly
    results = collection.query(
        query_texts=[search_question],
        n_results=5
    )

    docs = results["documents"][0]
    metadatas = results["metadatas"][0]

    print(f"Found {len(docs)} relevant documents")

    docs_text = "\n\n".join([doc[:800] for doc in docs])

    # Prompt for answer generation
    prompt = f"""
You are a helpful Data Structures tutor.

Use the retrieved documents to answer the question clearly.

If the documents contain relevant information, use them.
If they do not contain the answer, you may use your general knowledge.

Question:
{user_question}

Documents:
{docs_text}

Give a clear and concise explanation:
"""

    answer = generate_text(prompt).strip()

    answer, validation = validate_and_format_answer(answer)

    print("\nValidation Report:")
    for item in validation:
        print("-", item)

    # Extract source names from metadata
    sources = [m.get("source", "Unknown") for m in metadatas]
    log_interaction(user_question, search_question, sources, answer, validation)

    # Update chat history
    chat_history.append(HumanMessage(content=user_question))
    chat_history.append(AIMessage(content=answer))

    chat_history[:] = chat_history[-6:]

    print("\nAnswer:\n", answer)

    return answer


# -----------------------------
# CLI chat (optional)
# -----------------------------

def start_chat():

    print("Ask questions. Type 'quit' to exit. Type 'analytics' for stats.")

    while True:

        question = input("\nYour question: ")

        if question.lower() == "quit":
            print("Goodbye!")
            break

        if question.lower() == "analytics":
            show_analytics()
            continue

        ask_question(question)


if __name__ == "__main__":
    start_chat()