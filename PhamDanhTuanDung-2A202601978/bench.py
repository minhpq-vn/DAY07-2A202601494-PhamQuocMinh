from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))

from benchmark_common import run_benchmark
from src import FixedSizeChunker

chunker = FixedSizeChunker(chunk_size=450, overlap=50)

if __name__ == "__main__":
    raise SystemExit(run_benchmark("dung_fixed_450_overlap_50", chunker, ROOT))
