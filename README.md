# Hayroll Tests

Automated test runner for validating C to Rust transpilation using the C2Rust toolchain.
It builds, transpiles, and tests C programs from the CRUST benchmark, summarizing results in a structured JSON file.

The current results of the benchmark can be viewed at [`test_results.json`](test_results.json).

## Usage

## Evaluation

We have curated a dataset of C programs with different compile-time flags to evaluate Hayroll with in `test_programs`.

First, we compile and run the C programs on their own test suites with all different compile-flag combinations.

Next, we transpile the C program to Rust with Hayroll.

Finally, we verify Hayroll's transpilation by compiling, linking and testing the Rust code on the original C test suite for all combinations of compile-time flags.
