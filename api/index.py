import os
import sys
from pathlib import Path

# Add project root directory to sys.path so 'app' imports resolve cleanly
ROOT_DIR = str(Path(__file__).resolve().parent.parent)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Set serverless execution flags
os.environ["VERCEL"] = "1"
os.environ.setdefault("SYNC_PROCESSING", "true")

from starlette.types import ASGIApp, Receive, Scope, Send
from app.main import app as fastapi_app


class VercelPathFixMiddleware:
    """
    Middleware ensuring Vercel rewrite headers (x-forwarded-uri, x-matched-path)
    are respected so ASGI router matches the client's intended route.
    """
    def __init__(self, inner_app: ASGIApp):
        self.app = inner_app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http":
            path = scope.get("path", "")
            if path in ("/api/index.py", "/api/index", "/api", ""):
                headers = dict(scope.get("headers", []))
                matched_path = headers.get(b"x-matched-path", b"").decode("utf-8")
                forwarded_uri = headers.get(b"x-forwarded-uri", b"").decode("utf-8")
                target = forwarded_uri or matched_path
                if target:
                    scope["path"] = target.split("?")[0]
        await self.app(scope, receive, send)


app = VercelPathFixMiddleware(fastapi_app)
