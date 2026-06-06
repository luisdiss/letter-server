from fastapi import FastAPI
from contextlib import asynccontextmanager
import json
import uvicorn
from routes import get_routes

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        with open("config.json", "r") as file:
            app.state.config = json.load(file)
    except Exception as e:
        raise RuntimeError(f"Preprocessing failed: {e}")
    yield

app = FastAPI(lifespan=lifespan)
get_routes(app)

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )