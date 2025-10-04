# Autonomous AI Tutor Orchestrator

An intelligent middleware that connects a conversational AI tutor to educational tools (Note Maker, Flashcard Generator, Concept Explainer). It analyzes messages, extracts parameters, chooses the right tool via a LangGraph workflow, and returns formatted results.

## Tech Stack
- Backend: FastAPI, LangGraph, LangChain, SQLAlchemy (async), PostgreSQL (with SQLite fallback)
- Frontend: React (Vite) + Tailwind CSS

## Getting Started

### Backend
1. Configure environment:
   - Edit `backend/.env` if needed
   - Defaults:
     - `DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_tutor`
     - Fallback to SQLite file if Postgres unavailable
     - `TOOL_BASE_URL=http://localhost:8000`
2. Install and run:
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```
3. Open API docs at `http://localhost:8000/docs`.

### Frontend
1. Install and run:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
2. Open the app (default) `http://localhost:5173`.

## Features
- Context Analysis Engine: subject, topic, difficulty, sentiment
- Parameter Extraction: maps chat to tool schemas
- Tool Orchestrator: routes to `note_maker`, `flashcard_generator`, or `concept_explainer`
- State Management: users, chat sessions, messages, mastery levels persisted
- Validation and Error Handling: Pydantic schemas + unified error responses

## Project Structure
- `backend/` FastAPI app, routers, analysis, orchestrator
- `frontend/` React app with dashboard to test orchestration

## Example Usage
- Enter a message like:
  - "Make notes about photosynthesis"
  - "Create 10 flashcards for derivatives"
  - "Explain the Doppler effect for beginners"

This will show chosen tool, extracted parameters, and the tool output.
