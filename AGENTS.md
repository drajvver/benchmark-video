# Video Benchmark Platform — Agent Guide

## Project Structure
- `cli/` — Python CLI tool (Typer, Rich, psutil, py-cpuinfo)
- `web/backend/` — FastAPI + SQLModel + PostgreSQL
- `web/frontend/` — React + Vite + Tailwind CSS + Recharts

## Technology Choices
- **CLI**: Python for easy system introspection and ffmpeg subprocess handling
- **Backend**: FastAPI for async performance, SQLModel for type-safe ORM
- **Frontend**: React + Vite for fast dev, Tailwind for styling, Recharts for charts
- **Deployment**: Docker Compose with Nginx reverse proxy

## Build & Test

### CLI
```bash
cd cli
uv venv && uv pip install -e .
video-benchmark info
video-benchmark run --quick
```

### Backend
```bash
cd web/backend
uv venv && uv pip install -r requirements.txt
DATABASE_URL="sqlite:///./test.db" uv run uvicorn app.main:app --reload
```

### Frontend
```bash
cd web/frontend
npm install
npm run dev
```

### Docker Compose
```bash
docker compose up -d
```

## Code Style
- Python: PEP 8, type hints required
- TypeScript: Strict mode enabled
- Prefer functional components in React

## Testing
- Add tests in `cli/tests/` and `web/backend/tests/`
- Run backend tests with `pytest`
- Run frontend tests with `npm test`

## Database Migrations
Use Alembic for schema migrations:
```bash
cd web/backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```
