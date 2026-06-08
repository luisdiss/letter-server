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

Copy `.env.example` to `.env` and set your credentials:

```bash
cp .env.example .env
```

Then:

```bash
docker compose up --build
```

The server is available at `http://localhost:8000`.

The database is created automatically on first run using `init.sql`. Data persists in a Docker volume between restarts.

To stop and wipe everything (including the database volume):

```bash
docker compose down -v
```

Running with HTTPS (Caddy)
--------------------------
Point your domain's DNS A record at your server, then run:

```bash
DOMAIN=yourdomain.com docker compose --profile caddy up --build
```

Caddy fetches a Let's Encrypt certificate automatically on first boot and renews it without any manual steps. The server is available at `https://yourdomain.com`.

Port 8000 remains accessible directly — close it in your firewall if you don't want it reachable outside of Caddy.

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
All endpoints except `/login` and `POST /users` require `Authorization: Token <token>` in the header.

- `POST /users` — `{ "username": "u", "password": "p" }` → 201 on success, 409 if username taken, 400 if invalid
- `POST /login` — `{ "username": "u", "password": "p" }` → `{ "auth_token": "..." }`
- `GET /messages` — returns unread messages for the authenticated user
- `POST /messages` — `{ conversation_id, recipient_username, content, sent_at, expiration }` → `{ "conversation_id": ... }`
- `HEAD /users/{username}` — 200 if the user exists, 404 if not

Files
-----
- `server.py` — app entry and lifespan
- `routes.py` — API endpoints
- `dal.py` — all DB queries
- `auth.py` — session token creation and validation
- `utils.py` — helpers