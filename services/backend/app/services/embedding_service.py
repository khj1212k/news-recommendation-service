from __future__ import annotations

from typing import List

import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.preprocessing import normalize

from app.core.config import get_settings


class EmbeddingService:
    _sentence_model = None
    _sentence_model_name = None

    def __init__(self) -> None:
        settings = get_settings()
        self.provider = settings.embedding_provider
        self.model_name = settings.embedding_model
        self.dim = settings.embedding_dim
        self._vectorizer = None
        self._client = None
        self._model = None

        if self.provider == "hashing":
            self._vectorizer = HashingVectorizer(
                n_features=self.dim,
                alternate_sign=False,
                norm=None,
                ngram_range=(1, 2),
            )
        elif self.provider == "sentence-transformers":
            self._model = self._load_sentence_model(self.model_name)
        elif self.provider == "openai":
            from openai import OpenAI

            self._client = OpenAI()
        else:
            raise ValueError(f"Unsupported embedding provider: {self.provider}")

    @classmethod
    def _load_sentence_model(cls, model_name: str):
        if cls._sentence_model is None or cls._sentence_model_name != model_name:
            from sentence_transformers import SentenceTransformer

            cls._sentence_model = SentenceTransformer(model_name)
            cls._sentence_model_name = model_name
        return cls._sentence_model

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        if self.provider == "hashing":
            matrix = self._vectorizer.transform(texts)
            matrix = normalize(matrix, norm="l2")
            return matrix.toarray().astype(float).tolist()
        if self.provider == "sentence-transformers":
            embeddings = self._model.encode(texts, normalize_embeddings=True)
            vectors = np.asarray(embeddings).astype(float).tolist()
            if vectors and len(vectors[0]) != self.dim:
                raise ValueError(f"Embedding dim mismatch: expected {self.dim}, got {len(vectors[0])}")
            return vectors
        if self.provider == "openai":
            response = self._client.embeddings.create(model=self.model_name, input=texts)
            vectors = [item.embedding for item in response.data]
            if vectors and len(vectors[0]) != self.dim:
                raise ValueError(f"Embedding dim mismatch: expected {self.dim}, got {len(vectors[0])}")
            return vectors
        raise ValueError(f"Unsupported embedding provider: {self.provider}")

    def embed_text(self, text: str) -> List[float]:
        embeddings = self.embed_texts([text])
        if not embeddings:
            return [0.0] * self.dim
        return embeddings[0]
