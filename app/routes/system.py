import os
import re
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import structlog

from app.config import get_settings
from app.dependencies import get_current_user
from app.schemas.auth import CurrentUser

logger = structlog.get_logger()
router = APIRouter(prefix="/system", tags=["system"])


class AIStatusResponse(BaseModel):
    llm_provider: str
    model: str
    is_live_configured: bool
    masked_key: Optional[str] = None
    base_url: str


class AIConfigureRequest(BaseModel):
    gemini_api_key: str
    model: Optional[str] = "gemini-2.0-flash"


class AIConfigureResponse(BaseModel):
    success: bool
    message: str
    model: str
    is_live_configured: bool


@router.get("/ai-status", response_model=AIStatusResponse)
async def get_ai_status(
    current_user: CurrentUser = Depends(get_current_user),
) -> AIStatusResponse:
    settings = get_settings()
    key = settings.effective_llm_api_key
    is_configured = bool(key and key not in ("mock_key", "your_key_here", "dummy_key", "none", ""))

    masked = None
    if is_configured and key:
        if len(key) > 8:
            masked = f"{key[:4]}...{key[-4:]}"
        else:
            masked = "****"

    return AIStatusResponse(
        llm_provider=settings.LLM_PROVIDER,
        model=settings.LLM_MODEL,
        is_live_configured=is_configured,
        masked_key=masked,
        base_url=settings.LLM_BASE_URL,
    )


@router.post("/ai-config", response_model=AIConfigureResponse)
async def configure_ai_key(
    req: AIConfigureRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> AIConfigureResponse:
    clean_key = req.gemini_api_key.strip()
    if not clean_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gemini API Key cannot be empty.",
        )

    # Validate against Google AI Studio / Gemini API
    import urllib.request
    import urllib.error

    test_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={clean_key}"
    try:
        req_obj = urllib.request.Request(test_url, method="GET")
        with urllib.request.urlopen(req_obj, timeout=10.0) as resp:
            if resp.status != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Google AI Studio returned HTTP {resp.status}. Please check your API key.",
                )
    except urllib.error.HTTPError as http_err:
        err_body = http_err.read().decode("utf-8", errors="ignore")
        logger.warning("Gemini key validation failed", status=http_err.code, body=err_body)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid Google AI Studio Key (HTTP {http_err.code}). Please verify your key in Google AI Studio.",
        )
    except urllib.error.URLError as net_err:
        logger.warning("Gemini key validation network warning", exc=str(net_err))
        # If network restricted in container, check format
        if not clean_key.startswith("AIzaSy"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid key format. Google AI Studio keys typically start with 'AIzaSy'.",
            )
    except Exception as exc:
        logger.warning("Gemini key validation error", exc=str(exc))
        if not clean_key.startswith("AIzaSy"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid key format. Google AI Studio keys typically start with 'AIzaSy'.",
            )

    # Update runtime settings
    settings = get_settings()
    settings.GEMINI_API_KEY = clean_key
    settings.LLM_MODEL = req.model or "gemini-2.0-flash"
    settings.LLM_PROVIDER = "google"
    settings.LLM_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

    # Persist into .env file
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            new_lines = []
            gemini_seen = False
            model_seen = False
            for line in lines:
                if line.startswith("GEMINI_API_KEY="):
                    new_lines.append(f"GEMINI_API_KEY={clean_key}\n")
                    gemini_seen = True
                elif line.startswith("LLM_MODEL="):
                    new_lines.append(f"LLM_MODEL={settings.LLM_MODEL}\n")
                    model_seen = True
                elif line.startswith("LLM_BASE_URL="):
                    new_lines.append("LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/\n")
                else:
                    new_lines.append(line)
            if not gemini_seen:
                new_lines.append(f"GEMINI_API_KEY={clean_key}\n")
            if not model_seen:
                new_lines.append(f"LLM_MODEL={settings.LLM_MODEL}\n")
            with open(env_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
        except Exception as e:
            logger.warning("Could not persist GEMINI_API_KEY to .env", exc=str(e))

    return AIConfigureResponse(
        success=True,
        message="Google AI Studio Gemini 2.0 Flash successfully connected and active!",
        model=settings.LLM_MODEL,
        is_live_configured=True,
    )

