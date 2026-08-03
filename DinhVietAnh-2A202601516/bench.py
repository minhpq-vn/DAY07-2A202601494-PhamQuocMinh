from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))

from benchmark_common import run_benchmark
from src import SentenceChunker

chunker = SentenceChunker(max_sentences_per_chunk=3)

if __name__ == "__main__":
    raise SystemExit(run_benchmark("vietanh_sentence_3", chunker, ROOT))
