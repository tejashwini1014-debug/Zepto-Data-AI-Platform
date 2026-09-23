import os
import json
import urllib.request
from typing import TypedDict
MOCK_LLM = os.getenv("MOCK_LLM", "1")

import chromadb
from fastapi import FastAPI
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer

from langgraph.graph import StateGraph, END


# -----------------------------
# ChromaDB and document setup
# -----------------------------

DOCS_PATH = os.path.join(os.path.dirname(__file__), "docs")

# Load the local embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Create a local ChromaDB database
chroma_client = chromadb.PersistentClient(path="./chroma_db")

# Create or get the collection
collection = chroma_client.get_or_create_collection(
    name="zepto_policies",
    metadata={"hnsw:space": "cosine"}
)


def load_documents():
    """Load all 8 policy documents from the docs folder."""
    documents = []
    ids = []

    for i in range(1, 9):
        filename = f"doc_{i:02d}.txt"
        filepath = os.path.join(DOCS_PATH, filename)

        with open(filepath, "r", encoding="utf-8") as file:
            text = file.read().strip()

        documents.append(text)
        ids.append(filename.replace(".txt", ""))

    return documents, ids


def setup_chromadb():
    """Embed and store the 8 policy documents in ChromaDB."""
    documents, ids = load_documents()

    # Avoid adding duplicate documents every time the app starts
    existing = collection.get(ids=ids)

    existing_ids = set(existing.get("ids", []))

    new_documents = []
    new_ids = []

    for document, doc_id in zip(documents, ids):
        if doc_id not in existing_ids:
            new_documents.append(document)
            new_ids.append(doc_id)

    if new_documents:
        embeddings = embedding_model.encode(
            new_documents
        ).tolist()

        collection.add(
            ids=new_ids,
            documents=new_documents,
            embeddings=embeddings
        )

    print(f"ChromaDB contains {collection.count()} documents.")


setup_chromadb()

# -----------------------------
# Retrieval function
# -----------------------------

def retrieve_documents(query: str, top_k: int = 3):
    """Retrieve the most relevant policy documents."""
    
    query_embedding = embedding_model.encode(
        [query]
    ).tolist()[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    documents = results["documents"][0]
    ids = results["ids"][0]

    return documents, ids

# -----------------------------
# LangGraph state and nodes
# -----------------------------

class AgentState(TypedDict):
    query: str
    intent: str
    answer: str
    sources: list[str]
    confidence: float


def classify_intent(state: AgentState):
    """Classify the query using a deterministic keyword rule in mock mode."""

    query = state["query"].lower()

    policy_keywords = [
        "delivery",
        "return",
        "refund",
        "membership",
        "tracking",
        "cancel",
        "gift card",
        "support hours"
    ]

    if any(keyword in query for keyword in policy_keywords):
        intent = "policy_question"
    else:
        intent = "general_question"

    return {"intent": intent}


def retrieve_and_answer(state: AgentState):
    documents, ids = retrieve_documents(state["query"], top_k=3)

    if MOCK_LLM == "1":
        top_chunk_snippet = documents[0][:200]
        answer = f"Based on the retrieved context: {top_chunk_snippet}"

        return {
            "answer": answer,
            "sources": ids,
            "confidence": 1.0
        }

    else:
        context = "\n\n".join(
            f"[{doc_id}] {document}"
            for doc_id, document in zip(ids, documents)
        )

        prompt = POLICY_PROMPT_TEMPLATE.format(
            query=state["query"],
            context=context
        )

        validated_response = generate_validated_response(
            prompt,
            ids
        )

        return {
            "answer": validated_response.answer,
            "sources": validated_response.sources,
            "confidence": validated_response.confidence
        }


def direct_answer(state: AgentState):
    """Provide an answer for general questions."""

    if MOCK_LLM == "1":
        return {
            "answer": "I can only answer questions about Zepto policies right now.",
            "sources": [],
            "confidence": 1.0
        }

    prompt = f"""
Role:
You are a Zepto customer support assistant.

Task:
Answer the customer's question directly.

Question:
{state["query"]}

Format:
Return ONLY a valid JSON object with these fields:
{{
  "answer": "string",
  "sources": [],
  "confidence": 0.0
}}

Rules:
- This is a general question, so do not perform document retrieval.
- sources must be an empty list.
- confidence must be between 0 and 1.
- Do not use Markdown.
- Do not add extra text outside the JSON object.
"""

    validated_response = generate_validated_response(
        prompt,
        []
    )

    return {
        "answer": validated_response.answer,
        "sources": validated_response.sources,
        "confidence": validated_response.confidence
    }
# -----------------------------
# Build LangGraph workflow
# -----------------------------

workflow = StateGraph(AgentState)

# Add the three required nodes
workflow.add_node("classify_intent", classify_intent)
workflow.add_node("retrieve_and_answer", retrieve_and_answer)
workflow.add_node("direct_answer", direct_answer)

# Start with intent classification
workflow.set_entry_point("classify_intent")


def route_query(state: AgentState):
    """Route policy questions to retrieval and general questions to direct answer."""

    if state["intent"] == "policy_question":
        return "retrieve_and_answer"

    return "direct_answer"


# Conditional routing
workflow.add_conditional_edges(
    "classify_intent",
    route_query,
    {
        "retrieve_and_answer": "retrieve_and_answer",
        "direct_answer": "direct_answer"
    }
)

# Both branches finish the workflow
workflow.add_edge("retrieve_and_answer", END)
workflow.add_edge("direct_answer", END)

# Compile the graph
app_graph = workflow.compile()

# -----------------------------
# Pydantic API models
# -----------------------------

class AskRequest(BaseModel):
    query: str


class AskResponse(BaseModel):
    answer: str
    sources: list[str]
    confidence: float = Field(ge=0, le=1)

    # -----------------------------
# FastAPI application
# -----------------------------

app = FastAPI(title="Zepto Support Assistant")


@app.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest):
    """Answer a Zepto policy question."""

    initial_state = {
        "query": request.query,
        "intent": "",
        "answer": "",
        "sources": [],
        "confidence": 0.0
    }

    result = app_graph.invoke(initial_state)

    return AskResponse(
        answer=result["answer"],
        sources=result["sources"],
        confidence=result["confidence"]
    )

# -----------------------------
# Structured prompt template
# -----------------------------

POLICY_PROMPT_TEMPLATE = """
Role:
You are a Zepto customer support assistant.

Context:
Use only the retrieved Zepto policy context provided below.

Task:
Answer the customer's question using the retrieved context.

Format:
Return a clear and concise answer. Include the relevant policy information
and do not invent information that is not present in the context.

Length:
Keep the answer within 2-4 sentences.

Negative constraint:
Do not use outside knowledge, do not make up Zepto policies, and do not
claim information that is not supported by the retrieved context.

Few-shot example:
Customer question: What is the delivery fee?
Retrieved context: Standard delivery is free on orders over INR 149;
orders below this threshold incur a flat INR 25 delivery fee.
Answer: Standard delivery is free for orders over INR 149. Orders below
INR 149 have a flat INR 25 delivery fee.

Customer question:
{query}

Retrieved context:
{context}

Answer:
"""
def call_real_llm(prompt: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is required when MOCK_LLM=0."
        )

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0
    }

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        result = json.loads(response.read().decode("utf-8"))

    return result["choices"][0]["message"]["content"]


def generate_validated_response(
    prompt: str,
    fallback_sources: list[str]
) -> AskResponse:
    """
    Call the real LLM and validate its output against AskResponse.
    Retry up to 2 additional times if the output is invalid.
    """

    corrective_instruction = """
Your previous response did not match the required output schema.

Return ONLY a valid JSON object with exactly these fields:
{
  "answer": "string",
  "sources": ["source_id"],
  "confidence": 0.0
}

Rules:
- answer must be a string
- sources must be a list of strings
- confidence must be a number between 0 and 1
- do not use Markdown
- do not add any extra text outside the JSON object
"""

    current_prompt = prompt
    last_error = None

    for attempt in range(3):
        try:
            raw_output = call_real_llm(current_prompt)

            validated = AskResponse.model_validate_json(raw_output)

            return validated

        except Exception as error:
            last_error = error

            if attempt < 2:
                current_prompt = (
                    prompt
                    + "\n\n"
                    + corrective_instruction
                )

    return AskResponse(
        answer=f"[ERROR] Unable to generate a valid response after 3 attempts: {last_error}",
        sources=fallback_sources,
        confidence=0.0
    )