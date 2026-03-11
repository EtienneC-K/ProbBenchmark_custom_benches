#!/usr/bin/env python3

import argparse
import csv
import re
import statistics
import subprocess
from datetime import datetime
from pathlib import Path

try:
    import matplotlib.pyplot as plt
except ImportError as exc:
    raise SystemExit("matplotlib is required: pip install matplotlib") from exc


BENCHMARK_NAME = "bench_hashes"
THREAD_VALUE = 16 #TODO: not forget to change it on bigger mahcine
K_VALUE = 31
RAM_GB = 32
H_VALUES = [1, 2, 3, 4]
REPEATS = 1
BLOOM_BITS = 2**38 #TODO: not forget to change it on the other machine to fill 32Go
BUILD_FIRST = True
USE_INDEXED_FILE_FLAG = False
EXTRA_ARGS: list[str] = []

METRIC_PATTERNS = {
    "index_wall_s": r"index_wall_time_s\s+([0-9eE+.\-]+)",
    "index_cpu_s": r"index_cpu_time_s\s+([0-9eE+.\-]+)",
    "query_wall_s": r"query_wall_time_s\s+([0-9eE+.\-]+)",
    "query_cpu_s": r"query_cpu_time_s\s+([0-9eE+.\-]+)",
    #"fp": r"false positive rate\s+([0-9eE+.\-]+)",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("index_file")
    parser.add_argument("query_file")
    return parser.parse_args()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def results_dir() -> Path:
    path = Path(__file__).resolve().parent / "results"
    path.mkdir(parents=True, exist_ok=True)
    return path


def build_release(root: Path) -> None:
    if BUILD_FIRST:
        subprocess.run(["cargo", "build", "-r"], cwd=root, check=True)

def run_filter(root: Path, command: list[str]) -> dict[str, float]:
    completed = subprocess.run(
        command,
        cwd=root,
        check=True,
        text=True,
        capture_output=True,
    )
    metrics: dict[str, float] = {}
    for key, pattern in METRIC_PATTERNS.items():
        match = re.search(pattern, completed.stdout)
        if match is None:
            raise RuntimeError(
                f"Missing metric {key} in output.\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
            )
        metrics[key] = float(match.group(1))

    return metrics

def build_fastbloom_command(index_file: str, query_file: str, h: int) -> list[str]:
    command = [
        "./target/release/fastbloom",
        "--index-fasta",
        str(Path(index_file).expanduser()),
        "-k",
        str(K_VALUE),
        "--bloom-bits",
        str(BLOOM_BITS),
        "--hashes",
        str(h),
        "--threads",
        str(THREAD_VALUE),
        "--query-fasta",
        str(Path(query_file).expanduser()),
    ]
    command.extend(EXTRA_ARGS) #idk if it'll be used one day
    return command


def build_classic_command(index_file: str, query_file: str, h: int) -> list[str]:
    command = [
        "./target/release/classic_bloom",
        "--index-fasta",
        str(Path(index_file).expanduser()),
        "-k",
        str(K_VALUE),
        "--bloom-bits",
        str(BLOOM_BITS),
        "--hashes",
        str(h),
        "--threads",
        str(THREAD_VALUE),
        "--query-fasta",
        str(Path(query_file).expanduser()),
    ]
    command.extend(EXTRA_ARGS) #idk if it'll be used one day
    return command


def build_roaring_command(index_file: str, query_file: str, h: int) -> list[str]:
    command = [
        "./target/release/roaring_bloom",
        "--index-fasta",
        str(Path(index_file).expanduser()),
        "-k",
        str(K_VALUE),
        "--bloom-bits",
        str(BLOOM_BITS),
        "--hashes",
        str(h),
        "--threads",
        str(THREAD_VALUE),
        "--query-fasta",
        str(Path(query_file).expanduser()),
    ]
    command.extend(EXTRA_ARGS) #idk if it'll be used one day
    return command


def build_bf_rust_command(index_file: str, query_file: str, h: int) -> list[str]:
    command = [
        "./target/release/bloom_filter_rs",
        "--index-fasta",
        str(Path(index_file).expanduser()),
        "-k",
        str(K_VALUE),
        "--bloom-bits",
        str(BLOOM_BITS),
        "--hashes",
        str(h),
        "--threads",
        str(THREAD_VALUE),
        "--query-fasta",
        str(Path(query_file).expanduser()),
    ]
    command.extend(EXTRA_ARGS) #idk if it'll be used one day
    return command


def build_bloomfx_command(index_file: str, query_file: str, h: int) -> list[str]:
    command = [
        "./target/release/bloomfx",
        "--index-fasta",
        str(Path(index_file).expanduser()),
        "-k",
        str(K_VALUE),
        "--bloom-bits",
        str(BLOOM_BITS),
        "--hashes",
        str(h),
        "--threads",
        str(THREAD_VALUE),
        "--query-fasta",
        str(Path(query_file).expanduser()),
    ]
    command.extend(EXTRA_ARGS) #idk if it'll be used one day
    return command


def build_bloom_rs_command(index_file: str, query_file: str, h: int) -> list[str]:
    command = [
        "./target/release/bloom_rs",
        "--index-fasta",
        str(Path(index_file).expanduser()),
        "-k",
        str(K_VALUE),
        "--bloom-bits",
        str(BLOOM_BITS),
        "--hashes",
        str(h),
        "--threads",
        str(THREAD_VALUE),
        "--query-fasta",
        str(Path(query_file).expanduser()),
    ]
    command.extend(EXTRA_ARGS) #idk if it'll be used one day
    return command


def build_generic_command(index_file: str, query_file: str, h: int) -> list[str]:
    command = [
        "./target/release/generic_bloom",
        "--index-fasta",
        str(Path(index_file).expanduser()),
        "-k",
        str(K_VALUE),
        "--bloom-bits",
        str(BLOOM_BITS),
        "--hashes",
        str(h),
        "--threads",
        str(THREAD_VALUE),
        "--query-fasta",
        str(Path(query_file).expanduser()),
    ]
    command.extend(EXTRA_ARGS) #idk if it'll be used one day
    return command

def aggregate(metrics_list: list[dict[str, float]]) -> dict[str, float]:
    return {
        key: statistics.fmean(run[key] for run in metrics_list)
        for key in METRIC_PATTERNS
    }


def write_tsv(rows: list[dict[str, object]], output_path: Path) -> None:
    fieldnames = [
        "benchmark",
        "index_file",
        "query_file",
        "k",
        "ram_gb",
        "threads",
        "repeats",
        "h",
        "index_wall_s",
        "index_cpu_s",
        "query_wall_s",
        "query_cpu_s",
        #"fp",
    ]
    with output_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def plot_rows(rows: list[dict[str, object]], output_path: Path) -> None:
    x_values = [int(row["h"]) for row in rows]
    index_wall = [float(row["index_wall_s"]) for row in rows]
    index_cpu = [float(row["index_cpu_s"]) for row in rows]
    query_wall = [float(row["query_wall_s"]) for row in rows]
    query_cpu = [float(row["query_cpu_s"]) for row in rows]
    #false_positives = [float(row["fp"]) for row in rows]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharex=True)

    axes[0].plot(x_values, index_wall, marker="o", label="index wall")
    axes[0].plot(x_values, index_cpu, marker="o", label="index cpu")
    axes[0].set_title("Index Phase")
    axes[0].set_xlabel("h")
    axes[0].set_ylabel("seconds")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    axes[1].plot(x_values, query_wall, marker="o", label="query wall")
    axes[1].plot(x_values, query_cpu, marker="o", label="query cpu")
    axes[1].set_title("Query Phase")
    axes[1].set_xlabel("h")
    axes[1].set_ylabel("seconds")
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()

    #axes[2].plot(x_values, false_positives, marker="o", label="query wall")
    #axes[2].set_title("False positve rates")
    #axes[2].set_xlabel("m")
    #axes[2].set_ylabel("FP rate")
    #axes[2].grid(True, alpha=0.3)
    #axes[2].legend()

    fig.suptitle("bloomybloom benchmark: number of hashes sweep")
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    root = repo_root()
    build_release(root)

    fastbloom_rows: list[dict[str, object]] = []
    classic_rows: list[dict[str, object]] = []
    roaring_rows: list[dict[str, object]] = []
    bf_rust_rows: list[dict[str, object]] = []
    bloomfx_rows: list[dict[str, object]] = []
    bloom_rs_rows: list[dict[str, object]] = []
    generic_rows: list[dict[str, object]] = []
    for h in H_VALUES:
        metrics_list = [
            run_filter(root, build_fastbloom_command(args.index_file, args.query_file, h))
            for _ in range(REPEATS)
        ]
        metrics = aggregate(metrics_list)
        fastbloom_rows.append({
            "benchmark": BENCHMARK_NAME,
            "index_file": str(Path(args.index_file).expanduser()),
            "query_file": str(Path(args.query_file).expanduser()),
            "k": K_VALUE,
            "ram_gb": RAM_GB,
            "threads": THREAD_VALUE,
            "repeats": REPEATS,
            "h": h,
            **metrics,
        })

        metrics_list = [
            run_filter(root, build_classic_command(args.index_file, args.query_file, h))
            for _ in range(REPEATS)
        ]
        metrics = aggregate(metrics_list)
        classic_rows.append({
            "benchmark": BENCHMARK_NAME,
            "index_file": str(Path(args.index_file).expanduser()),
            "query_file": str(Path(args.query_file).expanduser()),
            "k": K_VALUE,
            "ram_gb": RAM_GB,
            "threads": THREAD_VALUE,
            "repeats": REPEATS,
            "h": h,
            **metrics,
        })

        metrics_list = [
            run_filter(root, build_roaring_command(args.index_file, args.query_file, h))
            for _ in range(REPEATS)
        ]
        metrics = aggregate(metrics_list)
        roaring_rows.append({
            "benchmark": BENCHMARK_NAME,
            "index_file": str(Path(args.index_file).expanduser()),
            "query_file": str(Path(args.query_file).expanduser()),
            "k": K_VALUE,
            "ram_gb": RAM_GB,
            "threads": THREAD_VALUE,
            "repeats": REPEATS,
            "h": h,
            **metrics,
        })

        metrics_list = [
            run_filter(root, build_bf_rust_command(args.index_file, args.query_file, h))
            for _ in range(REPEATS)
        ]
        metrics = aggregate(metrics_list)
        bf_rust_rows.append({
            "benchmark": BENCHMARK_NAME,
            "index_file": str(Path(args.index_file).expanduser()),
            "query_file": str(Path(args.query_file).expanduser()),
            "k": K_VALUE,
            "ram_gb": RAM_GB,
            "threads": THREAD_VALUE,
            "repeats": REPEATS,
            "h": h,
            **metrics,
        })

        metrics_list = [
            run_filter(root, build_bloomfx_command(args.index_file, args.query_file, h))
            for _ in range(REPEATS)
        ]
        metrics = aggregate(metrics_list)
        bloomfx_rows.append({
            "benchmark": BENCHMARK_NAME,
            "index_file": str(Path(args.index_file).expanduser()),
            "query_file": str(Path(args.query_file).expanduser()),
            "k": K_VALUE,
            "ram_gb": RAM_GB,
            "threads": THREAD_VALUE,
            "repeats": REPEATS,
            "h": h,
            **metrics,
        })

        metrics_list = [
            run_filter(root, build_bloom_rs_command(args.index_file, args.query_file, h))
            for _ in range(REPEATS)
        ]
        metrics = aggregate(metrics_list)
        bloom_rs_rows.append({
            "benchmark": BENCHMARK_NAME,
            "index_file": str(Path(args.index_file).expanduser()),
            "query_file": str(Path(args.query_file).expanduser()),
            "k": K_VALUE,
            "ram_gb": RAM_GB,
            "threads": THREAD_VALUE,
            "repeats": REPEATS,
            "h": h,
            **metrics,
        })

        metrics_list = [
            run_filter(root, build_generic_command(args.index_file, args.query_file, h))
            for _ in range(REPEATS)
        ]
        metrics = aggregate(metrics_list)
        generic_rows.append({
            "benchmark": BENCHMARK_NAME,
            "index_file": str(Path(args.index_file).expanduser()),
            "query_file": str(Path(args.query_file).expanduser()),
            "k": K_VALUE,
            "ram_gb": RAM_GB,
            "threads": THREAD_VALUE,
            "repeats": REPEATS,
            "h": h,
            **metrics,
        })

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = results_dir()
    fastbloom_tsv_path = out_dir / f"{BENCHMARK_NAME}-{timestamp}-fastbloom.tsv"
    classic_tsv_path = out_dir / f"{BENCHMARK_NAME}-{timestamp}-classicbloom.tsv"
    roaring_tsv_path = out_dir / f"{BENCHMARK_NAME}-{timestamp}-roaring.tsv"
    bf_rust_tsv_path = out_dir / f"{BENCHMARK_NAME}-{timestamp}-bf_rust.tsv"
    bloomfx_tsv_path = out_dir / f"{BENCHMARK_NAME}-{timestamp}-bloomfx.tsv"
    bloom_rs_tsv_path = out_dir / f"{BENCHMARK_NAME}-{timestamp}-bloom_rs.tsv"
    generic_tsv_path = out_dir / f"{BENCHMARK_NAME}-{timestamp}-generic.tsv"
    fastbloom_png_path = out_dir / f"{BENCHMARK_NAME}-{timestamp}-fastbloom.png"
    classic_png_path = out_dir / f"{BENCHMARK_NAME}-{timestamp}-classicbloom.png"
    roaring_png_path = out_dir / f"{BENCHMARK_NAME}-{timestamp}-roaring.png"
    bf_rust_png_path = out_dir / f"{BENCHMARK_NAME}-{timestamp}-bf_rust.png"
    bloomfx_png_path = out_dir / f"{BENCHMARK_NAME}-{timestamp}-bloomfx.png"
    bloom_rs_png_path = out_dir / f"{BENCHMARK_NAME}-{timestamp}-bloom_rs.png"
    generic_png_path = out_dir / f"{BENCHMARK_NAME}-{timestamp}-generic.png"
    write_tsv(fastbloom_rows, fastbloom_tsv_path)
    write_tsv(classic_rows, classic_tsv_path)
    write_tsv(roaring_rows ,roaring_tsv_path)
    write_tsv(bf_rust_rows ,bf_rust_tsv_path)
    write_tsv(bloomfx_rows ,bloomfx_tsv_path)
    write_tsv(bloom_rs_rows ,bloom_rs_tsv_path)
    write_tsv(generic_rows ,generic_tsv_path)
    plot_rows(fastbloom_rows, fastbloom_png_path)
    plot_rows(classic_rows, classic_png_path)
    plot_rows(roaring_rows ,roaring_png_path)
    plot_rows(bf_rust_rows ,bf_rust_png_path)
    plot_rows(bloomfx_rows ,bloomfx_png_path)
    plot_rows(bloom_rs_rows ,bloom_rs_png_path)
    plot_rows(generic_rows ,generic_png_path)
    print(fastbloom_tsv_path)
    print(classic_tsv_path)
    print(roaring_tsv_path)
    print(bf_rust_tsv_path)
    print(bloomfx_tsv_path)
    print(bloom_rs_tsv_path)
    print(generic_tsv_path)
    print(fastbloom_png_path)
    print(classic_png_path)
    print(roaring_png_path)
    print(bf_rust_png_path)
    print(bloomfx_png_path)
    print(bloom_rs_png_path)
    print(generic_png_path)


if __name__ == "__main__":
    main()
