from fastapi import FastAPI, HTTPException
from pymongo.errors import PyMongoError

from backend.database import mongo_client

app = FastAPI(title="Farm Wise AI API")


@app.get("/health")
def health():
    try:
        mongo_client.admin.command("ping")
    except PyMongoError as exc:
        raise HTTPException(status_code=503, detail="MongoDB is unavailable") from exc

    return {"api": "ok", "mongodb": "connected"}