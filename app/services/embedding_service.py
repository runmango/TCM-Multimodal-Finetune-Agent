from __future__ import annotations

import hashlib
import math
import re
from typing import List


DEFAULT_EMBEDDING_DIM = 128


def embed_text(text: str, dim: int = DEFAULT_EMBEDDING_DIM) -> List[float]:
    vector = [0.0] * dim
    for token in _tokenize(text):
        digest = hashlib.md5(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "little") % dim
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign
    return _normalize(vector)


def cosine_similarity(left: List[float], right: List[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return sum(a * b for a, b in zip(left, right))


def _tokenize(text: str) -> List[str]:
    normalized = (text or "").strip().lower()
    tokens = re.findall(r"[a-z0-9]{2,}|[\u4e00-\u9fff]", normalized)
    bigrams = [normalized[index : index + 2] for index in range(max(0, len(normalized) - 1))]
    return tokens + [item for item in bigrams if re.search(r"[\u4e00-\u9fff]", item)]


def _normalize(vector: List[float]) -> List[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm <= 0:
        return vector
    return [round(value / norm, 6) for value in vector]
