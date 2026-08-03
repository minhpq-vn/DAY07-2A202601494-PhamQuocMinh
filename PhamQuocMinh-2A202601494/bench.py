from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))

from benchmark_common import run_benchmark
from src import RecursiveChunker

chunker = RecursiveChunker(chunk_size=400)

if __name__ == "__main__":
    raise SystemExit(run_benchmark("minh_recursive_400", chunker, ROOT))
