from __future__ import annotations

import json

from app.services.vector_rag import build_vector_index


def main() -> None:
    result = build_vector_index()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
