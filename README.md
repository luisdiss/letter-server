Server — Letter
================

FastAPI backend. Handles auth, message storage, and delivery over a REST API.

Running locally
---------------
You need a Postgres database named `letter` running on localhost.

Create `src/.env` with your credentials:

```
DB_USER=postgres
DB_PASSWORD=yourpassword
```

Run the schema once on a fresh database:

```bash
psql -U postgres -d letter -f init.sql
```

Install and start:

```bash
pip install -e ".[dev]"
cd src
python server.py
```

Running with Docker
-------------------
This starts both the server and a Postgres container together. No local Postgres needed.

```bash
docker compose up --build
```

The database is created automatically on first run using `init.sql`. Data persists in a Docker volume between restarts.

To stop and wipe everything (including the database volume):

```bash
docker compose down -v
```

Pointing at an external database
---------------------------------
Run just the server image against any Postgres instance by passing env vars:

```bash
docker run -p 8000:8000 \
  -e DB_HOST=your-db-host \
  -e DB_USER=youruser \
  -e DB_PASSWORD=yourpassword \
  letter-server
```

You'll need to have run `init.sql` against that database first.

API
---
All endpoints except `/login` require `Authorization: Token <token>` in the header.

- `POST /login` — `{ "username": "u", "password": "p" }` → `{ "auth_token": "..." }`
- `GET /messages` — returns unread messages for the authenticated user
- `POST /messages` — `{ conversation_id, recipient_username, content, sent_at, expiration }`
- `HEAD /users/{username}` — 200 if the user exists, 404 if not

Files
-----
- `server.py` — app entry and lifespan
- `routes.py` — API endpoints
- `dal.py` — all DB queries
- `auth.py` — session token creation and validation
- `utils.py` — helpers