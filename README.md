# FlowGenAI

> **AI-powered business requirement analyzer and UML diagram generator.**  
> Paste a natural-language requirement, get structured use-case data, and auto-generate PlantUML / D2 diagrams in seconds.

---

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [Environment Variables](#environment-variables)
- [API Endpoints](#api-endpoints)
- [Usage](#usage)
- [Contributing](#contributing)

---

## Overview

FlowGenAI takes a plain-English business requirement and uses an LLM (Anthropic Claude) to:

1. **Analyze** the requirement → returns structured use-case data (actors, flows, pre/post-conditions, etc.)
2. **Generate diagrams** → produces PlantUML and D2 diagram source code ready to render.

The frontend is a React (Vite) SPA. The backend is a FastAPI service that proxies requests to the Anthropic API.

---

## Tech Stack

| Layer    | Technology |
|----------|------------|
| Frontend | React 19, Vite 8, Vanilla CSS |
| Backend  | Python, FastAPI, Uvicorn |
| AI       | Anthropic Claude (via `anthropic` SDK) |
| Diagrams | PlantUML, D2 |

---

## Project Structure

```
FlowGenAI/
├── frontend/               # React + Vite SPA
│   ├── App.jsx             # Main app shell (layout & state)
│   ├── Header.jsx          # Top navigation bar
│   ├── RequirementInput.jsx# Left panel — text input & analyze button
│   ├── AnalysisResults.jsx # Right panel — structured analysis view
│   ├── DiagramView.jsx     # Right panel — diagram source viewer
│   ├── api.js              # Fetch helpers (POST /api/analyze, /api/diagram)
│   ├── App.css             # Global styles & design tokens
│   ├── index.css           # Base resets
│   ├── main.jsx            # React entry point
│   └── vite.config.js      # Vite config (proxy → backend)
│
└── backend/                # FastAPI service
    ├── main.py             # All routes & LLM logic
    ├── requirements.txt    # Python dependencies
    ├── .env.example        # Environment variable template
    └── .env                # Local secrets (git-ignored)
```

---

## Getting Started

### Prerequisites

- **Node.js** ≥ 18  
- **Python** ≥ 3.10  
- An **Anthropic API key** — get one at [console.anthropic.com](https://console.anthropic.com)

---

### Backend Setup

```bash
# 1. Enter the backend directory
cd backend

# 2. Create & activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
copy .env.example .env      # Windows
# cp .env.example .env      # macOS / Linux
# Then edit .env and add your ANTHROPIC_API_KEY

# 5. Start the development server (runs on http://localhost:8000)
uvicorn main:app --reload
```

---

### Frontend Setup

```bash
# 1. Enter the frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Start the dev server (runs on http://localhost:5173)
npm run dev
```

> The Vite dev server proxies `/api` requests to `http://localhost:8000` automatically, so no extra CORS setup is needed during local development. In production the frontend calls `/api` on the same origin as itself — no extra configuration required.

---

## Environment Variables

### Backend — `backend/.env`

| Variable            | Required | Description                          |
|---------------------|----------|--------------------------------------|
| `ANTHROPIC_API_KEY` | ✅ Yes   | Your Anthropic Claude API key        |

> The frontend has **no environment variables** — it talks to `/api` on the same origin it is served from. No secrets or config files are needed on the frontend.

---

## API Endpoints

All endpoints are served by the FastAPI backend.

### `POST /api/analyze`

Analyzes a business requirement and returns structured use-case data.

**Request body:**
```json
{
  "requirement": "Users should be able to reset their password via email."
}
```

**Response:** Structured JSON with actors, use-case flows, pre/post-conditions, and more.

---

### `POST /api/diagram`

Generates PlantUML and D2 diagram source code from structured analysis data.

**Request body:** The full JSON object returned by `/api/analyze`.

**Response:**
```json
{
  "plantuml": "@startuml\n...\n@enduml",
  "d2": "..."
}
```

---

## Usage

1. Start both the backend and frontend servers (see [Getting Started](#getting-started)).
2. Open **http://localhost:5173** in your browser.
3. Type or paste a business requirement into the left panel.
4. Click **Analyze Requirement** — the AI will return structured use-case data.
5. Click **Generate Diagrams** — PlantUML and D2 source code will appear in the diagram view.

---

## Contributing

> 🚧 **Backend work in progress** — the backend implementation is being developed separately. Frontend is ready for integration.

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/your-feature`.
3. Commit your changes: `git commit -m "feat: add your feature"`.
4. Push to the branch: `git push origin feature/your-feature`.
5. Open a Pull Request.

---
