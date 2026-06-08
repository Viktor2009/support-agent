from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent.parent / "knowledge"

_chunks: list[dict] | None = None


def _split_markdown(text: str, source: str) -> list[dict]:
    chunks: list[dict] = []
    current_title = source
    lines: list[str] = []
    chunk_idx = 0

    for line in text.splitlines():
        if line.startswith("# "):
            if lines:
                chunks.append(
                    {
                        "id": f"{source}:{chunk_idx}",
                        "title": current_title,
                        "text": "\n".join(lines).strip(),
                    }
                )
                chunk_idx += 1
                lines = []
            current_title = line[2:].strip()
        else:
            lines.append(line)

    if lines:
        chunks.append(
            {
                "id": f"{source}:{chunk_idx}",
                "title": current_title,
                "text": "\n".join(lines).strip(),
            }
        )
    return [c for c in chunks if c["text"]]


def load_chunks() -> list[dict]:
    global _chunks
    if _chunks is not None:
        return _chunks

    all_chunks: list[dict] = []
    if KNOWLEDGE_DIR.exists():
        for path in sorted(KNOWLEDGE_DIR.glob("*.md")):
            all_chunks.extend(_split_markdown(path.read_text(encoding="utf-8"), path.stem))

    _chunks = all_chunks
    return _chunks


def reset_chunks() -> None:
    global _chunks
    _chunks = None
