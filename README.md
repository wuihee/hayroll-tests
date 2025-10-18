# Hayroll Tests

`metadata.json` contains metadata about each program in the CRUST benchmark, and is used to run the transpilation and tests.

The current results of the benchmark can be viewed at [`benchmark_summary.json`](./benchmark_summary.json).

## Prerequisites

Requires `CBench` directory from the CRUST benchmark to be copied into this repository.

## Usage

To transpile and run tests:

```sh
python benchmark.py
```

To view the results:

```sh
python analyze.py
```
