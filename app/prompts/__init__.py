"""Load prompt templates from YAML files."""

from functools import lru_cache
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent


@lru_cache
def _load_prompts(filename: str) -> dict[str, str]:
    path = PROMPTS_DIR / filename
    if not path.exists():
        return {}
    prompts: dict[str, str] = {}
    current_key: str | None = None
    lines: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not line.startswith(" ") and ":" in line:
            key_part = line.split(":", 1)[0].strip()
            if key_part and not key_part.startswith("-"):
                if current_key and lines:
                    prompts[current_key] = "\n".join(lines).strip("\n")
                current_key = key_part
                lines = []
                continue
        if current_key is not None:
            lines.append(line)
    if current_key and lines:
        prompts[current_key] = "\n".join(lines).strip("\n")
    return prompts


def get_prompt(name: str, *, filename: str = "intent.yaml", **kwargs: object) -> str:
    template = _load_prompts(filename).get(name, "")
    if not template:
        raise KeyError(f"Prompt '{name}' not found in {filename}")
    return template.format(**kwargs)
