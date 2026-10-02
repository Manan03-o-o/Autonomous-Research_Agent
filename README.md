# Autonomous AI Research Agent

A full-stack, autonomous research agent that orchestrates a multi-step workflow to generate professional, thoroughly researched, and verified reports. Built as a portfolio project for a Senior Full Stack AI Engineer.

## Project Overview

This agent does not just pass a user prompt to an LLM. It autonomously:
1. Breaks down complex questions into sub-questions (Planner)
2. Generates queries and searches the web (Searcher via Tavily)
3. Extracts and chunks content from sources (Extractor)
4. Generates lightweight embeddings and stores them in PostgreSQL (FastEmbed + pgvector)
5. Extracts specific claims and confidence scores (Evidence)
6. Evaluates if the evidence is sufficient, or repeats the search (Critic)
7. Generates a structured Markdown report (Reporter via Groq)
8. Verifies all citations match the evidence (Verifier)

## Architecture & Technology Stack

- **LLM Provider:** Groq (Using `llama3-70b-8192` via `groq` SDK)
- **Search Provider:** Tavily Search API
- **Embeddings:** FastEmbed (`BAAI/bge-small-en-v1.5`, 384 dimensions, ONNX runtime - no PyTorch/GPU required)
- **Backend:** Python 3.11, FastAPI, SQLAlchemy, Alembic
- **Database:** PostgreSQL with `pgvector`
- **Cache / Messaging:** Redis
- **Frontend:** React, TypeScript, Vite, Tailwind v4
- **Real-Time:** Server-Sent Events (SSE) stream progress directly to the UI.
- **Infrastructure:** Docker & Docker Compose

## Setup & Local Development

### 1. Environment Variables
Create a `.env` file in the root directory (copy from `.env.example`):
```env
GROQ_API_KEY=your_groq_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

### 2. Start the Backend via Docker
Ensure Docker Desktop is running, then execute:
```bash
docker-compose up -d --build
```
This will start PostgreSQL (with vector support), Redis, and the FastAPI backend on `http://localhost:8000`.

### 3. Start the Frontend
In a new terminal:
```bash
cd frontend
npm install
npm run dev
```
Access the dashboard at `http://localhost:5173`.

## Database Schema

- **ResearchJob:** Tracks the high-level request, user question, status, and completion time.
- **Source:** Web pages found during research (URL, title).
- **ExtractedContent:** Text chunks and their 384-dimensional vector embeddings.
- **Claim:** Factual claims extracted from text with a confidence score.
- **Evidence:** Snippets of text backing up a Claim, linked to a Source.
- **Report:** The final generated markdown report.

## Future Improvements

- Add hybrid search (keyword + vector).
- Implement Playwright for JavaScript-heavy pages (currently uses BeautifulSoup).
- Add PDF export functionality on the frontend.
