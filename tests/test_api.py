# LogicForge Backend

A FastAPI + SQLAlchemy backend for LogicForge: The Programmer's Brain, an educational programming adventure game.

## Features

- Guest player profile creation and persistent progress using SQLite
- Eight regions, missions, and unlockable progression
- 30 coding and logic challenge seeds across conditions, loops, arrays, functions, debugging, algorithms, maze routes, and boss objectives
- Restricted visual-program interpreter for maze challenges and safe validation
- XP, coins, rank tracking, achievements, and skill unlocks
- Adaptive difficulty response driven by player score
- CORS support for React + TypeScript frontend integration
- JSON API endpoints for the full gameplay loop

## Stack

- Python 3.12+
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic
- Pytest

## Setup

1. Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the backend:

```bash
uvicorn app.main:app --reload
```

The app will create `logicforge.db` automatically on first startup.

## Security note

The backend never executes raw player Python code inside the server. Maze and visual challenges are evaluated through a restricted instruction interpreter that allows only a fixed set of commands and rejects unsafe patterns.

## Gameplay loop

1. Create a guest player with `POST /api/v1/players/guest`
2. Fetch world data with `GET /api/v1/world`
3. Load a mission and challenge detail
4. Submit a solution with `POST /api/v1/challenges/{id}/submit`
5. Ask for hints with `POST /api/v1/challenges/{id}/hint`
6. Check rewards and progression with `GET /api/v1/progression`
7. Continue unlocking missions as progress is saved to SQLite

## Example API flow

```bash
curl -X POST http://localhost:8000/api/v1/players/guest \
  -H "Content-Type: application/json" \
  -d '{"guest_name":"Nova"}'
```

Then use the returned `id` in the `X-Player-ID` header for subsequent requests.

## Testing

```bash
pytest -q
```

## Frontend integration

The backend CORS configuration includes common local frontend ports such as `3000` and `5173`, and all JSON responses are plain FastAPI/Pydantic objects ready for a React + TypeScript app.
