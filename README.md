Server — Letter
================

FastAPI backend. Run this if you want to self-host Letter under your own domain and redistribute the client pointing at your server.

Running with Docker
-------------------
Copy `.env.example` to `.env` and fill in your credentials and domain:

```bash
cp .env.example .env
```

```
DB_USER=youruser
DB_PASSWORD=yourpassword
DOMAIN=yourdomain.com
```

Point your domain's DNS A record at your server, then run:

```bash
docker compose --profile caddy up -d
```

Caddy fetches a Let's Encrypt certificate automatically and renews it without any manual steps. The server is available at `https://yourdomain.com`.

Point the client at your server by changing `server_url` in the client's `src/settings.txt`:

```json
{
    "server_url": "https://yourdomain.com",
    "expiration": null
}
```

API
---
All endpoints except `/login` and `POST /users` require `Authorization: Token <token>` in the header.

- `POST /users` — `{ "username": "u", "password": "p" }` → 201 on success, 409 if taken, 400 if invalid
- `POST /login` — `{ "username": "u", "password": "p" }` → `{ "auth_token": "..." }`
- `GET /messages` — returns unread messages for the authenticated user
- `POST /messages` — `{ conversation_id, recipient_username, content, sent_at, expiration }` → `{ "conversation_id": ... }`
- `HEAD /users/{username}` — 200 if the user exists, 404 if not
