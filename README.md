# Zepto Data & AI Platform

An end-to-end AI/ML capstone project covering data engineering, analytics and machine learning, and a GenAI-powered support assistant.

## Project Overview

This project is divided into three modules:

1. **Module 1 – Data Pipeline**
   - Web scraping of book data
   - Data cleaning and transformation
   - GBP to INR conversion
   - SQLite database creation
   - SQL analysis using JOIN queries
   - Pandas-based analysis

2. **Module 2 – Analytics and Machine Learning**
   - Titanic dataset analysis
   - Exploratory Data Analysis (EDA)
   - Data preprocessing
   - Classification models
   - Imbalance handling
   - Hyperparameter tuning
   - Regression metrics
   - Complete saved ML pipeline

3. **Module 3 – GenAI Support Assistant**
   - Zepto policy document ingestion
   - Local text embeddings
   - ChromaDB vector database
   - Semantic retrieval
   - LangGraph workflow
   - Structured responses using Pydantic
   - FastAPI REST API
   - Mock LLM mode
   - Docker support

---

## Project Structure

```text
Zepto-Data-AI-Platform/
│
├── data_pipeline/
│   ├── books.db
│   ├── queries.py
│   ├── query_outputs.txt
│   ├── README.md
│   ├── requirements.txt
│   └── scrape_and_load.py
│
├── analytics/
│   ├── 01_eda.ipynb
│   ├── 02_modeling.ipynb
│   ├── README.md
│   ├── model_pipeline.joblib
│   └── titanic.csv
│
├── support_assistant/
│   ├── docs/
│   │   ├── doc_01.txt
│   │   ├── doc_02.txt
│   │   ├── doc_03.txt
│   │   ├── doc_04.txt
│   │   ├── doc_05.txt
│   │   ├── doc_06.txt
│   │   ├── doc_07.txt
│   │   └── doc_08.txt
│   ├── chroma_db/
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
│
└── README.md