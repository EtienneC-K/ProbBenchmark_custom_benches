# ProbBenchmark

Rust command-line benchmarks for k-mer indexing and querying on FASTA files using multiple Bloom filter implementations.

The project currently provides three binaries:

- `fastbloom`: benchmark based on [`fastbloom`](https://crates.io/crates/fastbloom)
- `classic_bloom`: benchmark based on [`bloom-filters`](https://crates.io/crates/bloom-filters)
- `roaring_bloom`: benchmark based on [`roaring-bloom-filter`](https://crates.io/crates/roaring-bloom-filter)

Each binary:

- reads one FASTA file to index
- extracts all valid DNA k-mers (`A`, `C`, `G`, `T`)
- inserts indexed k-mers into a Bloom filter
- reads a second FASTA file to query
- checks query k-mers against the Bloom filter
- reports timing, CPU usage, memory usage, and k-mer counts

## Build

The repository is configured for aggressive release optimization:

- `opt-level = 3`
- `lto = "fat"`
- `codegen-units = 1`
- `panic = "abort"` for release
- `strip = "symbols"`
- default `-C target-cpu=native`

Because `target-cpu=native` is enabled in [.cargo/config.toml](/home/nadine/Code/ProbBenchmark/.cargo/config.toml), release binaries are optimized for the machine that builds them and may be less portable to older CPUs.

Build all release binaries:

```bash
cargo build -r
```

Build a specific binary:

```bash
cargo build -r --bin fastbloom
cargo build -r --bin classic_bloom
cargo build -r --bin roaring_bloom
```

Run tests:

```bash
cargo test
```

## Output Binaries

After `cargo build -r`, the binaries are available in:

```bash
target/release/fastbloom
target/release/classic_bloom
target/release/roaring_bloom
```

## Usage

All three binaries use the same CLI.

Required arguments:

- `--index-fasta <FASTA>`
- `--query-fasta <FASTA>`
- `-k, --kmer-size <INT>`

Optional Bloom filter parameters:

- `--bloom-bits <INT>`
- `--bloom-bytes <INT>`
- `--hashes <INT>`
- `--false-positive-rate <FLOAT>` default: `0.01`

Optional runtime parameters:

- `--threads <INT>`
- `--batch-bases <INT>` default: `33554432`

Example with explicit Bloom size and hash count:

```bash
./target/release/fastbloom \
  --index-fasta ref.fa \
  --query-fasta query.fa \
  --kmer-size 31 \
  --bloom-bits 1000000000 \
  --hashes 7 \
  --threads 16
```

Example with automatic sizing:

```bash
./target/release/classic_bloom \
  --index-fasta ref.fa \
  --query-fasta query.fa \
  --kmer-size 31 \
  --false-positive-rate 0.001 \
  --threads 16
```

Example with the roaring implementation:

```bash
./target/release/roaring_bloom \
  --index-fasta ref.fa \
  --query-fasta query.fa \
  --kmer-size 31 \
  --bloom-bytes 134217728 \
  --hashes 6
```

## Reported Metrics

Each run prints tab-separated key/value pairs:

- `index_wall_time_s`
- `query_wall_time_s`
- `index_cpu_time_s`
- `query_cpu_time_s`
- `indexed_kmers`
- `queried_kmers`
- `query_positive_kmers`
- `bloom_bits`
- `bloom_bytes`
- `bloom_hashes`
- `max_ram_bytes`
- `max_ram_mib`
- `threads`
- `precount_pass`

Notes:

- `max_ram_bytes` and `max_ram_mib` are the process peak RSS for the whole run, not separate per-phase peaks.
- `precount_pass=true` means the program performed an extra pass over the indexed FASTA to estimate the number of k-mers because `--bloom-bits` or `--hashes` was not fully specified.
- only k-mers composed entirely of `A`, `C`, `G`, and `T` are indexed or queried

## Implementation Notes

### `fastbloom`

- Uses `fastbloom::AtomicBloomFilter`
- Supports concurrent insertions directly
- Best option in this repository for parallel indexing throughput

### `classic_bloom`

- Uses the classic Bloom filter from `bloom-filters`
- Indexing uses one shared Bloom filter protected by a mutex
- Avoids duplicate filter copies, but mutation is synchronized

### `roaring_bloom`

- Uses `roaring-bloom-filter::StableBloomFilter`
- Indexing also uses one shared Bloom filter protected by a mutex
- This crate requires sized values for insertion and lookup, so k-mers are hashed to `u64` keys before insertion and query

## Crate Origins

### Bloom filter crates

- `fastbloom`
  - Crate: <https://crates.io/crates/fastbloom>
  - Documentation: <https://docs.rs/fastbloom/0.17.0>
  - Repository: <https://github.com/tomtomwombat/fastbloom>

- `bloom-filters`
  - Crate: <https://crates.io/crates/bloom-filters>
  - Documentation: <https://docs.rs/bloom-filters/0.1.2>
  - Repository: <https://github.com/nervosnetwork/bloom-filters>
  - Notes: Rust port of BoomFilters, as stated by the crate metadata

- `roaring-bloom-filter`
  - Crate: <https://crates.io/crates/roaring-bloom-filter>
  - Documentation: <https://docs.rs/roaring-bloom-filter/0.2.0>
  - Repository: <https://github.com/oliverdding/roaring-bloom-filter-rs>
  - License note: this crate is published under `AGPL-3.0`

### Supporting crates used by this project

- `clap`
  - Crate: <https://crates.io/crates/clap>
  - Repository: <https://github.com/clap-rs/clap-rs>
  - Purpose: CLI argument parsing

- `rayon`
  - Crate: <https://crates.io/crates/rayon>
  - Repository: <https://github.com/rayon-rs/rayon>
  - Purpose: parallel batch and sequence processing

- `anyhow`
  - Crate: <https://crates.io/crates/anyhow>
  - Repository: <https://github.com/dtolnay/anyhow>
  - Purpose: ergonomic error handling

- `libc`
  - Crate: <https://crates.io/crates/libc>
  - Repository: <https://github.com/rust-lang/libc>
  - Purpose: `getrusage` access for CPU and peak RAM reporting

## Project Layout

```text
src/lib.rs                  Shared FASTA parsing, k-mer traversal, metrics, reporting
src/bin/fastbloom.rs        fastbloom benchmark binary
src/bin/classic_bloom.rs    bloom-filters benchmark binary
src/bin/roaring_bloom.rs    roaring-bloom-filter benchmark binary
.cargo/config.toml          default target-cpu=native configuration
```
