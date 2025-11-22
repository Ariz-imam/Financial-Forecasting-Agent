1. Project Overview

This project implements an AI-powered Financial Forecasting Agent for Tata Consultancy Services (TCS).
The goal is to generate a qualitative business outlook forecast using:

Quarterly financial report PDFs

Earnings call transcripts

A local LLM-based RAG system for semantic search and summarization

A structured, machine-readable JSON forecast output

Logging of all requests and responses into a local SQLite database

The system is completely offline, runs without external APIs, and is designed to be easy to set up locally.

2. High-Level Architecture

The project is organized into several modular components:

a) FinancialDataExtractor Tool

Reads quarterly PDF reports.

Extracts key metrics such as revenue, net profit, operating margin, and EPS.

Computes quarter-on-quarter trends.

Returns structured numeric data used by the forecasting agent.

b) QualitativeAnalysis (RAG) Tool

Loads earnings call transcripts.

Splits and embeds them using a local sentence-transformer model.

Stores and retrieves embeddings using Chroma vector DB.

Sends retrieved text to a local Mistral LLM.

Produces structured summaries including:

Themes

Management sentiment

Forward-looking statements

Risks and opportunities

c) Agent Orchestrator

Coordinates both tools.

Merges financial data + qualitative insights.

Generates the final forecast using the local LLM.

Ensures the final output is a well-structured JSON object.

d) FastAPI Server

Serves a /forecast endpoint.

Accepts requests specifying how many quarters to analyze.

Handles validation, execution, and response formatting.

e) Database Logging (SQLite Only)

Every request and response is saved to a local SQLite database file.

Provides transparency and traceability.

Avoids the need for a full MySQL setup during local development.

SQLite was intentionally chosen as the default because it makes the project easy to run anywhere, while still meeting the assignment requirement of logging all requests.

3. Local LLM Setup

To ensure offline capability and reproducibility, the project uses:

Local Mistral 7B (GGUF) Model

Runs through llama-cpp-python.

Does not require any cloud API keys.

Works entirely offline.

Generates summaries, structured JSON, and forecasts.

You simply download a .gguf model file (such as Mistral-7B-Instruct Q4_K_M) and set its path in the .env file.

4. SQLite Database

This project uses SQLite as the only database during local development.

No setup or installation required.

The database file is automatically created.

FastAPI automatically logs each request and response.

Tables are created via init_db.py.

Database file location:

db/app_fallback.sqlite

5. Folder Structure Explanation

tcs-forecast-agent/
│
├── app/
│   ├── main.py              → FastAPI server and forecast endpoint
│   ├── orchestrator.py       → Combines tools and generates final forecast
│   ├── schemas.py            → Request models
│
├── tools/
│   ├── financial_extractor.py → Extracts numeric metrics from PDFs
│   ├── qualitative_rag.py     → Transcript analysis using RAG + local LLM
│
├── scripts/
│   └── build_vector_store.py  → Creates embeddings for transcripts
│
├── db/
│   ├── db.py                  → SQLite engine + session management
│   ├── models.py              → RequestLog database model
│
├── data/
│   ├── financial_reports/     → Quarterly financial PDFs (input)
│   └── transcripts/           → Earnings call transcript PDFs (input)
│
├── init_db.py                 → Creates SQLite tables
├── requirements.txt           → Python dependencies
├── .env.example               → Template environment file
├── README.md                  → Project documentation

Each directory has a single purpose and keeps logic modular and easy to maintain.

6. Environment Setup Instructions

Follow these steps to run the system locally.

Step 1: Create a .env file

Copy .env.example → .env

Update:

The path to your downloaded .gguf model

Keep MYSQL_URL empty (SQLite mode)

Example:

MYSQL_URL=
DATA_ROOT=./data
CHROMA_DB_DIR=./db/chroma
LLAMA_MODEL_PATH=C:/LLM_Models/mistral-7b-instruct-v0.2.Q4_K_M.gguf
LLAMA_N_CTX=2048
SENTENCE_EMBED_MODEL=all-MiniLM-L6-v2

Step 2: Create virtual environment

python -m venv .venv

Activate (PowerShell):

.venv\Scripts\Activate.ps1

Step 3: Install dependencies

pip install -r requirements.txt

Step 4: Build vector store

python -m scripts.build_vector_store

Step 5: Initialize SQLite database

python init_db.py


Step 6: Run the FastAPI server

uvicorn app.main:app --reload --port 8000

Our local API is now running at:

http://127.0.0.1:8000

7. How to Use the Forecast Endpoint

Endpoint:

POST /forecast


Example request body:

{
  "quarters": 2,
  "company": "TCS"
}

We will receive a structured JSON forecast containing:

Financial trends

Management sentiment

Forward-looking statements

Risks and opportunities

Overall forecast for the upcoming quarter

All requests and responses are logged automatically into the SQLite database.

8. How the Forecast Gets Generated (End-to-End)

You upload quarterly PDFs + transcript PDFs into data/.

Vector store is built from transcripts.

When a forecast request is made:

The system extracts numeric metrics from financial PDFs.

The RAG tool retrieves the most relevant transcript chunks.

The local Mistral LLM summarizes them into structured insights.

The orchestrator merges numeric + qualitative data.

A final JSON forecast is produced.

The complete request + response is stored in SQLite.

This workflow demonstrates:

multi-step reasoning

tool usage

retrieval-augmented generation

controlled JSON outputs

logging and reproducibility

9. Notes for Reviewers

Entire system is offline and reproducible.

Tools are modular, testable, and cleanly separated.

Local LLM usage is documented in the README and .env.

SQLite fallback ensures the reviewer can run the project instantly.

Logging satisfies the assignment requirement for DB persistence.

No external API keys or services required.