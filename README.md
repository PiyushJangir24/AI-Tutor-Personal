# Autonomous AI Tutor Orchestrator

An intelligent middleware that connects a conversational AI tutor to multiple educational tools. It analyzes messages, extracts parameters, routes to the right tool, and formats responses.

## Tech Stack
- Backend: Python + FastAPI
- Agent Frameworks: LangGraph + LangChain (heuristic-based usage)
- Database: PostgreSQL (async) with SQLAlchemy (falls back to SQLite if POSTGRES_URL not set)
- Frontend: React (Vite) + Tailwind CSS

## Run locally

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Setup env (edit as needed)
cp .env .env.local 2>/dev/null || true
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Swagger is available at `http://localhost:8000/docs`.

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Vite dev server runs at `http://localhost:5173` and proxies `/api` to the FastAPI backend.

## Project Structure
```
backend/
  main.py
  orchestrator.py
  schemas.py
  models.py
  db.py
  tools/
    mock_tools.py
  requirements.txt
  .env
frontend/
  src/
    App.jsx
    main.jsx
    index.css
  index.html
  package.json
  tailwind.config.js
  postcss.config.js
  vite.config.js
  .env
```

## Notes
- The backend uses simple heuristics for analysis and parameter extraction to keep the demo self-contained.
- Tool endpoints are mocked: `/note_maker`, `/flashcard_generator`, `/concept_explainer`.
- User state, mastery, and chat history are stored. If PostgreSQL is unavailable, it will use a local SQLite file `dev.db`.
