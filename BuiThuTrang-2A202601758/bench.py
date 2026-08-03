from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))

from benchmark_common import HeadingChunker, run_benchmark

chunker = HeadingChunker(chunk_size=500)

if __name__ == "__main__":
    raise SystemExit(run_benchmark("trang_heading_500", chunker, ROOT))
