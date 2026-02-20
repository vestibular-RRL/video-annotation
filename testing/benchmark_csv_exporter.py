"""
Benchmark script for CSVExporter performance and UI-freeze proxy metrics.

Usage:
    python testing/benchmark_csv_exporter.py --rows 300000 --runs 3 --chunk-size 5000
"""

import argparse
import gc
import os
import random
import sys
import tempfile
import tracemalloc
from statistics import mean
from time import perf_counter

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.core.csv_exporter import CSVExporter


def generate_data(rows: int):
    labels = ["0", "downbeat", "upbeat", "left beat", "right beat", "mix"]
    return [
        {
            "Frame#": frame,
            "Annotation": random.choice(labels),
        }
        for frame in range(1, rows + 1)
    ]


def run_single_benchmark(exporter: CSVExporter, data, method: str, chunk_size: int):
    with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{method}.csv") as temp_file:
        output_path = temp_file.name

    try:
        gc.collect()
        tracemalloc.start()
        start_wall = perf_counter()

        if method == "fast":
            metrics = exporter.export_annotations_to_csv_with_metrics(
                data=data,
                file_path=output_path,
                method="fast",
                chunk_size=chunk_size,
                process_callback=lambda: None,
            )
        else:
            metrics = exporter.export_annotations_to_csv_with_metrics(
                data=data,
                file_path=output_path,
                method="pandas",
            )

        wall_seconds = perf_counter() - start_wall
        _, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        file_size_bytes = os.path.getsize(output_path) if os.path.exists(output_path) else 0

        return {
            "success": bool(metrics.get("success", False)),
            "method": method,
            "duration_seconds": float(metrics.get("duration_seconds", wall_seconds)),
            "wall_seconds": wall_seconds,
            "max_block_seconds": float(metrics.get("max_block_seconds", wall_seconds)),
            "chunk_count": int(metrics.get("chunk_count", 1) or 1),
            "peak_memory_mb": peak_bytes / (1024 * 1024),
            "file_size_mb": file_size_bytes / (1024 * 1024),
        }
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)


def summarize(results, method: str):
    method_results = [r for r in results if r["method"] == method and r["success"]]
    if not method_results:
        return None

    return {
        "method": method,
        "runs": len(method_results),
        "avg_duration_seconds": mean(r["duration_seconds"] for r in method_results),
        "avg_wall_seconds": mean(r["wall_seconds"] for r in method_results),
        "avg_max_block_seconds": mean(r["max_block_seconds"] for r in method_results),
        "avg_peak_memory_mb": mean(r["peak_memory_mb"] for r in method_results),
        "avg_file_size_mb": mean(r["file_size_mb"] for r in method_results),
    }


def main():
    parser = argparse.ArgumentParser(description="Benchmark CSVExporter methods")
    parser.add_argument("--rows", type=int, default=300000, help="Number of annotation rows to generate")
    parser.add_argument("--runs", type=int, default=3, help="Number of benchmark runs per method")
    parser.add_argument("--chunk-size", type=int, default=5000, help="Chunk size for fast export callbacks")
    args = parser.parse_args()

    print("=== CSV Exporter Benchmark ===")
    print(f"Rows: {args.rows:,}")
    print(f"Runs per method: {args.runs}")
    print(f"Fast method chunk size: {args.chunk_size:,}")

    print("\nGenerating synthetic annotation data...")
    data = generate_data(args.rows)
    print("Data generation complete.")

    exporter = CSVExporter()
    all_results = []

    methods = ["pandas", "fast"]
    for method in methods:
        print(f"\nRunning {method} benchmarks...")
        for run_index in range(1, args.runs + 1):
            result = run_single_benchmark(exporter, data, method, args.chunk_size)
            all_results.append(result)
            print(
                f"  Run {run_index}: "
                f"duration={result['duration_seconds']:.3f}s, "
                f"max_block={result['max_block_seconds']:.3f}s, "
                f"peak_mem={result['peak_memory_mb']:.2f}MB"
            )

    pandas_summary = summarize(all_results, "pandas")
    fast_summary = summarize(all_results, "fast")

    print("\n=== Summary (averages) ===")
    if pandas_summary:
        print(
            f"pandas -> duration={pandas_summary['avg_duration_seconds']:.3f}s, "
            f"max_block={pandas_summary['avg_max_block_seconds']:.3f}s, "
            f"peak_mem={pandas_summary['avg_peak_memory_mb']:.2f}MB"
        )
    if fast_summary:
        print(
            f"fast   -> duration={fast_summary['avg_duration_seconds']:.3f}s, "
            f"max_block={fast_summary['avg_max_block_seconds']:.3f}s, "
            f"peak_mem={fast_summary['avg_peak_memory_mb']:.2f}MB"
        )

    if pandas_summary and fast_summary:
        duration_speedup = pandas_summary["avg_duration_seconds"] / max(fast_summary["avg_duration_seconds"], 1e-9)
        memory_reduction_pct = (
            (pandas_summary["avg_peak_memory_mb"] - fast_summary["avg_peak_memory_mb"])
            / max(pandas_summary["avg_peak_memory_mb"], 1e-9)
        ) * 100
        block_reduction_pct = (
            (pandas_summary["avg_max_block_seconds"] - fast_summary["avg_max_block_seconds"])
            / max(pandas_summary["avg_max_block_seconds"], 1e-9)
        ) * 100

        print("\n=== Improvement Indicators ===")
        print(f"Speedup (pandas/fast): {duration_speedup:.2f}x")
        print(f"Peak memory reduction: {memory_reduction_pct:.1f}%")
        print(f"Max blocking-window reduction: {block_reduction_pct:.1f}%")
        print("(Blocking-window is a UI-freeze proxy: lower is better.)")


if __name__ == "__main__":
    main()
