import logging
import uuid

from fastapi import Depends, Request
from fastapi.responses import JSONResponse
from supabase import Client, create_client

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)


class AppException(Exception):
    def __init__(self, status_code: int, code: str, message: str, request_id: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.request_id = request_id


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "status": exc.status_code,
                "request_id": exc.request_id,
            }
        },
    )


def get_supabase(settings: Settings = Depends(get_settings)) -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_key)


async def get_current_user(
    request: Request,
    supabase: Client = Depends(get_supabase),
) -> dict[str, str]:
    request_id = str(uuid.uuid4())
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        logger.error("Missing Authorization header | request_id=%s", request_id)
        raise AppException(
            status_code=401,
            code="AUTH_TOKEN_MISSING",
            message="Authorization header is required.",
            request_id=request_id,
        )

    parts = auth_header.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        logger.error("Malformed Authorization header | request_id=%s", request_id)
        raise AppException(
            status_code=401,
            code="AUTH_TOKEN_INVALID",
            message="Authorization header must be 'Bearer <token>'.",
            request_id=request_id,
        )

    token = parts[1]
    token_suffix = token[-8:] if len(token) > 8 else token

    try:
        user_response = supabase.auth.get_user(token)
        user = user_response.user

        if user is None:
            logger.error(
                "JWT verification returned no user | token=...%s | request_id=%s",
                token_suffix,
                request_id,
            )
            raise AppException(
                status_code=401,
                code="AUTH_TOKEN_INVALID",
                message="Invalid or expired authentication token.",
                request_id=request_id,
            )

        logger.info(
            "Authenticated user_id=%s | request_id=%s", user.id, request_id
        )
        return {"id": user.id, "email": user.email or ""}

    except AppException:
        raise
    except Exception as exc:
        logger.error(
            "JWT verification failed | token=...%s | error=%s | request_id=%s",
            token_suffix,
            str(exc),
            request_id,
        )
        raise AppException(
            status_code=401,
            code="AUTH_TOKEN_INVALID",
            message="Invalid or expired authentication token.",
            request_id=request_id,
        ) from exc
