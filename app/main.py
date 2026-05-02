from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
import os

from app.kvstore import KVStoreService
from app.url_service import URLService
from app.schemas import (
    URLRequestShortenRequest,
    URLResponseShortenResponse,
    URLResponseRedirect,
    URLResponseStats,
)

app = FastAPI()

# -------------------------
# Config
# -------------------------

HOST = os.getenv("REDIS_HOST", "localhost")
PORT = int(os.getenv("REDIS_PORT", 6379))
PASSWORD = os.getenv("REDIS_PASSWORD", None)
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


# -------------------------
# Dependency Injection
# -------------------------

def get_kv_store():
    # no manual connect() needed anymore
    store = KVStoreService(host=HOST, port=PORT, password=PASSWORD)
    try:
        yield store
    finally:
        store.close()


def get_url_service(store: KVStoreService = Depends(get_kv_store)):
    return URLService(store, base_url=BASE_URL)


# -------------------------
# Health
# -------------------------

@app.get("/", status_code=status.HTTP_200_OK)
def root():
    return {"message": "URL Shortener API"}


@app.get("/ping", status_code=status.HTTP_200_OK)
def ping(store: KVStoreService = Depends(get_kv_store)):
    try:
        store.client.ping()
        return {"status": "connected", "message": "pong"}
    except Exception:
        return {"status": "disconnected"}


# -------------------------
# Core APIs
# -------------------------

@app.post(
    "/shorten",
    response_model=URLResponseShortenResponse,
    status_code=status.HTTP_201_CREATED,
)
def shorten_url(
    req: URLRequestShortenRequest,
    service: URLService = Depends(get_url_service),
):
    result = service.shorten(req.long_url)

    return URLResponseShortenResponse(
        key=result["key"],
        long_url=result["long_url"],
        short_url=result["short_url"],
    )

@app.get(
    "/{key}",
    response_model=URLResponseRedirect,
    status_code=status.HTTP_200_OK,
)
def get_url(
    key: str,
    service: URLService = Depends(get_url_service),
):
    result = service.resolve(key)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="URL not found",
        )

    return URLResponseRedirect(
        key=result["key"],
        long_url=result["long_url"],
        status_code=status.HTTP_302_FOUND,
    )


@app.get(
    "/stats/{key}",
    response_model=URLResponseStats,
    status_code=status.HTTP_200_OK,
)
def get_stats(
    key: str,
    service: URLService = Depends(get_url_service),
):
    data = service.get_stats(key)

    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="URL not found",
        )

    return data


@app.delete(
    "/{key}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_url(
    key: str,
    store: KVStoreService = Depends(get_kv_store),
):
    deleted = store.delete(f"short:{key}")

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="URL not found",
        )

    return None