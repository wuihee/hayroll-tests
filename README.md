# Hayroll Tests

The current results of the benchmark can be viewed at [`test_results.json`](test_results.json).

## Prerequisites

Requires `CBench` directory from the CRUST benchmark to be copied into this repository.

## Usage

To transpile and run tests:

```sh
python3 scripts/run_tests.py
```

To generate metadata used to run tests:

```sh
python3 scripts/generate_metadata.py
```

## Notes

Currently excluding `skp` program because it always seems to hang.
