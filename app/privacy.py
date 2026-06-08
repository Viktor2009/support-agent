import re
from typing import Any

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"\+?\d[\d\s\-()]{8,}\d")


def mask_email(value: str) -> str:
    if "@" not in value:
        return value
    local, domain = value.split("@", 1)
    if len(local) <= 1:
        masked_local = "*"
    else:
        masked_local = local[0] + "*" * (len(local) - 1)
    return f"{masked_local}@{domain}"


def mask_pii_text(text: str) -> str:
    masked = EMAIL_RE.sub(lambda m: mask_email(m.group(0)), text)
    return PHONE_RE.sub("[PHONE]", masked)


def mask_payload(data: Any) -> Any:
    if isinstance(data, dict):
        return {key: mask_payload(value) for key, value in data.items()}
    if isinstance(data, list):
        return [mask_payload(item) for item in data]
    if isinstance(data, str):
        return mask_pii_text(data)
    return data
