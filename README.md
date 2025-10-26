# Hayroll Tests

Automated test runner for validating C to Rust transpilation using the C2Rust toolchain.
It builds, transpiles, and tests C programs from the CRUST benchmark, summarizing results in a structured JSON file.

The current results of the benchmark can be viewed at [`test_results.json`](test_results.json).

## Prerequisites

Requires `CBench` directory from the CRUST benchmark to be copied into this repository.

Other dependencies include: `python3`, `bear`, `make`, `gcc`, `cargo`, `c2rust`.

## Usage

To transpile all C programs and run their tests:

```sh
python3 scripts/run_tests.py
```

To generate metadata used to run tests:

```sh
python3 scripts/generate_metadata.py
```

## Notes

Currently excluding `skp` program because it always seems to hang.
