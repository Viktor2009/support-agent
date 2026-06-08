from langchain_core.callbacks.base import BaseCallbackHandler

from app.config import settings


def get_langfuse_handler(session_id: str | None = None) -> BaseCallbackHandler | None:
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        return None
    try:
        from langfuse.callback import CallbackHandler
    except ImportError:
        return None

    return CallbackHandler(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
        session_id=session_id,
    )


def graph_invoke_config(session_id: str, *, stream_tokens: bool = False) -> dict:
    config: dict = {
        "configurable": {
            "thread_id": session_id,
            "stream_tokens": stream_tokens,
        }
    }
    handler = get_langfuse_handler(session_id)
    if handler is not None:
        config["callbacks"] = [handler]
    return config
