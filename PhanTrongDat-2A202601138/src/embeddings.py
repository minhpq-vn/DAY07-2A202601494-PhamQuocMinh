from __future__ import annotations

import hashlib
import math

# Multilingual model suitable for the Vietnamese corpora used in this Lab.
# The local backend remains optional; required checkpoints use MockEmbedder.
LOCAL_EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_PROVIDER_ENV = "EMBEDDING_PROVIDER"


class MockEmbedder:
    """Deterministic embedding backend used by tests and default classroom runs."""

    def __init__(self, dim: int = 64) -> None:
        self.dim = dim
        self._backend_name = "mock embeddings fallback"  # dummy fallback 

    def __call__(self, text: str) -> list[float]:
        digest = hashlib.md5(text.encode()).hexdigest()  # hash input string    
        seed = int(digest, 16) # convert hex string to int
        vector = []
        for _ in range(self.dim):
            seed = (seed * 1664525 + 1013904223) & 0xFFFFFFFF # đây là công thức LCG (Linear Congruential Generator), có tác dụng sinh ra số giả ngẫu nhiên
            vector.append((seed / 0xFFFFFFFF) * 2 - 1) # chia cho 0xFFFFFFFF để đưa về khoảng [0,1]
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0 # tính độ lớn của vector
        return [value / norm for value in vector] # chia cho độ lớn của vector để vector có độ dài bằng 1


class LocalEmbedder:
    """Sentence Transformers-backed local embedder."""

    def __init__(self, model_name: str = LOCAL_EMBEDDING_MODEL) -> None:  # khởi tạo đối tượng Embedder với tên model được truyền vào
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self._backend_name = model_name
        self.model = SentenceTransformer(model_name) # tải mô hình về và gán cho self.model

    def __call__(self, text: str) -> list[float]: # phương thức này sẽ được gọi khi đối tượng được truyền vào như một hàm, tức là khi ta gọi embedder(text)
        embedding = self.model.encode(text, normalize_embeddings=True) # sử dụng mô hình để mã hóa văn bản
        if hasattr(embedding, "tolist"):
            return embedding.tolist() # trả về dạng list
        return [float(value) for value in embedding] # trả về dạng list


class OpenAIEmbedder: # OpenAIEmbedder là một lớp được sử dụng để mã hóa văn bản thành vector embedding bằng cách sử dụng API của OpenAI. Lớp này kế thừa từ lớp base Embedder và triển khai phương thức __call__ để thực hiện việc mã hóa.
    """OpenAI embeddings API-backed embedder."""

    def __init__(self, model_name: str = OPENAI_EMBEDDING_MODEL) -> None:
        from openai import OpenAI

        self.model_name = model_name
        self._backend_name = model_name
        self.client = OpenAI() # khởi tạo client để gửi request lên API của OpenAI

    def __call__(self, text: str) -> list[float]:
        response = self.client.embeddings.create(model=self.model_name, input=text) # gọi API của OpenAI để mã hóa văn bản
        return [float(value) for value in response.data[0].embedding] # trả về dạng list


_mock_embed = MockEmbedder()
