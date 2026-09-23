# Zepto Support Assistant

A small GenAI customer support service for answering Zepto policy questions using local document retrieval, embeddings, ChromaDB, LangGraph, and FastAPI.

## Features

- Uses the provided 8 Zepto policy documents.
- Generates embeddings using `all-MiniLM-L6-v2`.
- Stores document embeddings in ChromaDB.
- Retrieves the top 3 relevant documents using cosine similarity.
- Uses LangGraph for query routing.
- Supports policy and general questions.
- Provides a deterministic offline mock mode by default.
- Provides an optional real LLM mode using the OpenAI API.
- Validates LLM responses using Pydantic.
- Retries invalid LLM responses up to 2 additional times.
- Provides a FastAPI `/ask` endpoint.

## Project Structure

```text
support_assistant/
├── docs/
│   ├── doc_01.txt
│   ├── doc_02.txt
│   ├── doc_03.txt
│   ├── doc_04.txt
│   ├── doc_05.txt
│   ├── doc_06.txt
│   ├── doc_07.txt
│   └── doc_08.txt
├── chroma_db/
├── main.py
├── requirements.txt
├── Dockerfile
└── README.md
```

## Architecture

The application follows this flow:

```text
User Query
    |
    v
FastAPI /ask
    |
    v
LangGraph
    |
    v
classify_intent
    |
    +----------------------+
    |                      |
    v                      v
Policy Question       General Question
    |                      |
    v                      v
retrieve_and_answer   direct_answer
    |
    v
ChromaDB Retrieval
    |
    v
Top 3 Relevant Documents
    |
    v
Answer Generation
    |
    v
Pydantic Validation
    |
    v
JSON Response
```

### Component Mapping

| Stage | Component | File / Node |
|---|---|---|
| Document ingestion | Document loader | `main.py` - `load_documents()` |
| Embedding | Sentence Transformer | `all-MiniLM-L6-v2` |
| Vector storage | ChromaDB | `chroma_db/` |
| Intent classification | LangGraph node | `classify_intent` |
| Retrieval and policy answer | LangGraph node | `retrieve_and_answer` |
| General answer | LangGraph node | `direct_answer` |
| Output validation | Pydantic | `AskResponse` |
| API | FastAPI | `/ask` |
| Containerization | Docker | `Dockerfile` |

## Document Ingestion and Embeddings

The application loads all 8 policy documents from the `docs/` directory.

Each document is embedded using:

```text
all-MiniLM-L6-v2
```

The embeddings are stored in ChromaDB using cosine similarity.

The application automatically creates the ChromaDB collection and stores the documents when `main.py` starts.

## Retrieval

For policy questions:

1. The user query is converted into an embedding.
2. ChromaDB searches the stored document embeddings.
3. The top 3 most relevant documents are retrieved.
4. The retrieved document IDs are returned as sources.
5. The answer is generated using the retrieved context.

Retrieval is performed in both mock mode and real LLM mode.

## LangGraph Workflow

The LangGraph workflow contains three named nodes:

### 1. `classify_intent`

Classifies the query as either:

```text
policy_question
```

or:

```text
general_question
```

In mock mode, this uses a keyword-based heuristic.

Policy keywords include:

```text
delivery
return
refund
membership
tracking
cancel
gift card
support hours
```

### 2. `retrieve_and_answer`

Used for policy questions.

It retrieves the top 3 relevant documents from ChromaDB.

In mock mode, the response is generated deterministically from the top retrieved document.

### 3. `direct_answer`

Used for general questions.

In mock mode, it returns a fixed response because the assistant is designed to answer Zepto policy questions.

## Mock Mode

Mock mode is the default.

The environment variable is:

```text
MOCK_LLM=1
```

If `MOCK_LLM` is not set, the application also defaults to mock mode.

The `MOCK_LLM` setting affects answer generation and general-question handling. `classify_intent` always uses the deterministic keyword heuristic, while policy retrieval always uses the real ChromaDB retrieval path. With `MOCK_LLM=1`, answers are deterministic and offline; with `MOCK_LLM=0`, the optional real LLM generation path is used.

Mock mode:

- Does not call an external LLM API.
- Does not require an API key.
- Uses deterministic keyword-based routing.
- Performs real ChromaDB retrieval for policy questions.
- Returns deterministic responses.
- Uses confidence `1.0`.

### Example policy response

```json
{
  "answer": "Based on the retrieved context: Zepto delivers grocery and household essentials...",
  "sources": [
    "doc_01",
    "doc_05",
    "doc_02"
  ],
  "confidence": 1.0
}
```

### Example general response

```json
{
  "answer": "I can only answer questions about Zepto policies right now.",
  "sources": [],
  "confidence": 1.0
}
```

## Optional Real LLM Mode

The application also contains an optional real LLM path.

Set:

```text
MOCK_LLM=0
```

and provide:

```text
OPENAI_API_KEY
```

In real mode:

- Policy questions use retrieved context.
- A structured prompt is used.
- General questions are answered directly.
- The LLM response is validated using the Pydantic `AskResponse` model.
- Invalid responses are retried up to 2 additional times.
- If all attempts fail, a clearly marked error response is returned.

## Structured Prompt

The policy prompt contains:

- Role
- Context
- Task
- Format
- Length
- Negative constraint
- Few-shot example

The negative constraint prevents the model from using outside knowledge or inventing Zepto policies.

## Output Schema

The API response follows this schema:

```json
{
  "answer": "string",
  "sources": ["source_id"],
  "confidence": 0.0
}
```

The `confidence` value must be between `0` and `1`.

## Running Locally

Open PowerShell inside the `support_assistant` folder.

Install dependencies:

```powershell
pip install -r requirements.txt
```

Run the FastAPI server:

```powershell
python -m uvicorn main:app --port 7860
```

The API will be available at:

```text
http://127.0.0.1:7860
```

Swagger documentation:

```text
http://127.0.0.1:7860/docs
```

## API Endpoint

### POST `/ask`

The API accepts a JSON request containing a `query`.

### Example 1 — Policy question

Request:

```json
{
  "query": "What is the delivery fee?"
}
```

Raw JSON response from the locally tested FastAPI application:

```json
{
  "answer": "Based on the retrieved context: Zepto delivers grocery and household essentials to serviceable pin codes within 10 to 30 minutes of order confirmation, depending on the customer's delivery zone and current order volume. Standard del",
  "sources": [
    "doc_01",
    "doc_05",
    "doc_02"
  ],
  "confidence": 1.0
}
```

This query contains the keyword `delivery`, so `classify_intent` routes it to `retrieve_and_answer`. ChromaDB retrieves the top 3 relevant documents.

### Example 2 — General question

Request:

```json
{
  "query": "What is Python?"
}
```

Raw JSON response from the locally tested FastAPI application:

```json
{
  "answer": "I can only answer questions about Zepto policies right now.",
  "sources": [],
  "confidence": 1.0
}
```

This query does not contain any of the configured Zepto policy keywords, so `classify_intent` routes it to `direct_answer`. No document retrieval is performed.

## Docker

A Dockerfile is included for containerized deployment.

Dockerfile command:

```text
uvicorn main:app --host 0.0.0.0 --port 7860
```

To build the image:

```powershell
docker build -t zepto-support-assistant .
```

To run the container:

```powershell
docker run -p 7860:7860 zepto-support-assistant
```

Docker is optional for local development.

## Summary

The Zepto Support Assistant combines:

```text
Policy Documents
       |
       v
Sentence Transformers
       |
       v
ChromaDB
       |
       v
LangGraph
       |
       +---- Policy ---> Retrieval ---> Answer
       |
       +---- General --> Direct Answer
       |
       v
Pydantic Validation
       |
       v
FastAPI
       |
       v
JSON Response
```

The default mock mode provides a fully offline deterministic baseline, while the optional real LLM mode extends the system with generated responses and schema validation.