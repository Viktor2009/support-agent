import hashlib
import math
import re

EMBED_DIM = 64


def tokenize(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-zA-Zа-яА-ЯёЁ0-9]+", text.lower()) if len(w) > 2]


def mock_embedding(text: str) -> list[float]:
    """Deterministic pseudo-embedding for offline/tests."""
    vector = [0.0] * EMBED_DIM
    for token in tokenize(text):
        digest = hashlib.md5(token.encode()).hexdigest()
        value = int(digest, 16)
        for index in range(EMBED_DIM):
            bit = (value >> (index % 32)) & 1
            vector[index] += 1.0 if bit else -1.0
    norm = math.sqrt(sum(component * component for component in vector)) or 1.0
    return [component / norm for component in vector]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))
