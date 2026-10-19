from pathlib import Path
import json
from dotenv import load_dotenv
load_dotenv()
from openai import OpenAI


client = OpenAI()


def load_documents():
    data = []
    folder = Path(__file__).resolve().parent / "docs"
    # если docs лежит не рядом со скриптом — временно верни свой абсолютный путь
    for file in folder.glob("*.txt"):
        with open(file, encoding="utf-8") as f:
            data.append({
                "source": file.name,
                "text": f.read(),
            })
    return data


def make_chunks(size=300, overlap=50):
    chunks = []
    for doc in load_documents():
        text = doc["text"]
        start = 0
        while start < len(text):
            piece = text[start : start + size]
            if piece.strip():
                chunks.append({
                    "source": doc["source"],
                    "text": piece,
                })
            start += size - overlap
            if size - overlap <= 0:
                break
    return chunks


def embed(text: str) -> list[float]:
    """Текст → вектор чисел (смысл текста)."""
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )
    return response.data[0].embedding


def cosine(a: list[float], b: list[float]) -> float:
    """Насколько два вектора похожи. Ближе к 1 = похожее по смыслу."""
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


INDEX_PATH = Path(__file__).resolve().parent / "embeddings.json"


def build_index():
    chunks = make_chunks()
    index = []
    for chunk in chunks:
        index.append({
            "source": chunk["source"],
            "text": chunk["text"],
            "embedding": embed(chunk["text"]),
        })
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False)
    return index


def load_index():
    if not INDEX_PATH.exists():
        return build_index()
    with open(INDEX_PATH, encoding="utf-8") as f:
        return json.load(f)


def search_docs(query: str, top_k: int = 3, min_score: float = 0.25) -> str:
    index = load_index()
    if not index:
        return "Нет документов для поиска."

    query_vec = embed(query)

    scored = []
    for item in index:
        score = cosine(query_vec, item["embedding"])
        scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    best = [(s, c) for s, c in scored[:top_k] if s >= min_score]

    if not best:
        return "Ничего не найдено"

    parts = []
    for score, chunk in best:
        parts.append(
            f"[{chunk['source']}] (score={score:.3f})\n{chunk['text'].strip()}"
        )
    return "\n\n".join(parts)


if __name__ == "__main__":
    print("--- список ---")
    print(search_docs("список"))
    print("\n--- словарь ---")
    print(search_docs("словарь"))
    print("\n--- что умеет агент ---")
    print(search_docs("что умеет агент"))
    print("\n--- крипта ---")
    print(search_docs("крипта"))