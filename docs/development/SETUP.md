# Development Setup Guide

## Prerequisites
- **Docker & Docker Compose**
- **Python 3.10+** (if running locally without Docker)
- **Node.js 20+** (if developing frontend locally)

## Quick Start (Docker - Recommended)

1. **Clone & Configure**
   ```bash
   git clone <repo>
   cd Victoria
   cp config/environments/.env.example config/environments/.env.local
   # Edit .env.local with your API keys (Groq, Twilio, etc.)
   ```

2. **Run Environment**
   ```bash
   docker-compose -f docker-compose.dev.yml up --build
   ```
   - Backend: http://localhost:8000
   - Frontend: http://localhost:5173
   - API Docs: http://localhost:8000/docs

## Manual Setup (No Docker)

### Backend
1. **Virtual Env**
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r backend/requirements.txt
   ```

2. **Run Server**
   ```bash
   # Make sure you are in project root
   uvicorn backend.interfaces.http.main:app --reload
   ```

### Frontend
1. **Install & Run**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Testing
```bash
# Unit Tests
pytest tests/unit

# Integration Tests (Requires local DB/mocks)
pytest tests/integration

# E2E Tests (Requires running services)
pytest tests/e2e
```
