Server — Letter
================

A focused FastAPI backend for storing and serving messages. The server is intentionally compact and organized for clarity and testability.

Highlights
----------
- FastAPI REST API
- Simple DAL layer using SQLAlchemy and parameterized SQL
- Argon2 password hashing and session tokens
- Modular layout: `routes`, `dal`, `auth`, `utils`

Quickstart
----------
1. Create and activate a virtualenv:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. (Optional) Edit `config.json` to adjust limits and settings.

4. Run the server for development:

```bash
python server.py
```

API Endpoints
-------------
- `POST /login` — body: `{ "username": "u", "password": "p" }` → returns `{ "auth_token": "..." }`
- `GET /messages` — header `Authorization: Token <token>` → returns a JSON list of messages
- `POST /messages` — send a message with `{ conversation_id, recipient_username, content, sent_at, expiration }`
- `HEAD /users/{username}` — check user existence

Testing & CI notes
------------------
- Add unit tests for DAL functions and API endpoints using `pytest` and FastAPI `TestClient`.
- Add a GitHub Actions workflow to run linting, types, and tests on pull requests.

Deployment
----------
- Add a `Dockerfile` and `docker-compose.yml` for demo deployments.
- In production, run behind an HTTPS reverse proxy and enable proper DB credentials handling.

Files of interest
-----------------
- `server.py` — app entry and lifespan
- `routes.py` — API endpoints
- `dal.py` — DB interactions
- `auth.py` — session management
- `utils.py` — helper functions

Next improvements
-----------------
- Integration tests and a containerized demo
- Basic rate limiting and stricter request validation
