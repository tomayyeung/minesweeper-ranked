import os, logging.config
from fastapi import FastAPI, WebSocket

from server.server import handle_main

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s %(levelname)s %(name)s: %(message)s"
        }
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "default",
        }
    },
    "root": {
        "level": LOG_LEVEL,
        "handlers": ["stdout"]
    },
    "loggers": {
        # leave uvicorn loggers to behave normally but direct access/error to stdout
        "uvicorn.error": {"level": LOG_LEVEL, "handlers": ["stdout"], "propagate": False},
        "uvicorn.access": {"level": "INFO", "handlers": ["stdout"], "propagate": False},
    },
}

logging.config.dictConfig(LOGGING_CONFIG)

app = FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.websocket("/ws/{room_name}")
async def websocket_endpoint(ws: WebSocket, room_name: str):
    await ws.accept()
    await handle_main(ws, room_name)