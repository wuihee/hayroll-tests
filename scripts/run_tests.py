"""
crust_test_runner.py

This script automates testing of C-to-Rust transpilation using C2Rust.

For each program listed in `crust_metadata.json`, it:
  1. Builds the original C source using `make` (wrapped with `bear` for compilation DB).
  2. Transpiles the C source into Rust using `c2rust`.
  3. Builds the transpiled Rust code using Cargo.
  4. Links and runs the original C tests against the generated Rust library.
  5. Collects and summarizes results in `test_results.json`.

Usage:
    python crust_test_runner.py
"""

import json
import subprocess
from enum import Enum, auto
from pathlib import Path

# Path to the metadata file containing program info.
METADATA_FILE = Path("crust_metadata.json")


class Stage(Enum):
    """Enumeration of distinct build/test stages in the transpilation pipeline."""

    C_BUILD = auto()
    TRANSPILE = auto()
    RUST_BUILD = auto()
    RUST_LINK = auto()
    RUST_TEST = auto()

    def __str__(self) -> str:
        """Return a user-friendly, snake_case name for logs and JSON output."""
        names = {
            Stage.C_BUILD: "c_build",
            Stage.TRANSPILE: "transpile",
            Stage.RUST_BUILD: "rust_build",
            Stage.RUST_LINK: "rust_link",
            Stage.RUST_TEST: "rust_test",
        }
        return names[self]


def run_command(command: str, path: str) -> tuple[bool, str]:
    """
    Run a shell command in a given directory.

    Args:
        command (str): The shell command to execute.
        path (str): The working directory where the command is run.

    Returns:
        tuple[bool, str]:
            - True and empty string if successful.
            - False and stderr output if the command fails.
    """
    result = subprocess.run(
        command, cwd=path, capture_output=True, text=True, shell=True
    )
    return result.returncode == 0, result.stderr


def run_stage(stage: Stage, command: str, path: str, result_dict: dict) -> bool:
    """
    Run a build/test stage and update the result dictionary if it fails.

    Note that `result_dict` is mutated with the new results.

    Args:
        stage (Stage): The current pipeline stage.
        command (str): The command to execute for this stage.
        path (str): The working directory.
        result_dict (dict): The dictionary tracking program or test results.

    Returns:
        bool: True if the stage succeeded, False if it failed.
    """
    success, error = run_command(command, path)
    if not success:
        result_dict.update(status="failed", stage_failed=str(stage), error=error)
        return False
    return True


def run_tests(metadata_file: Path):
    """
    Run the entire C-to-Rust transpilation and testing pipeline.

    Reads `metadata_file` for program definitions, executes each stage,
    and writes a detailed summary to `test_results.json`.

    Args:
        metadata_file (Path): Path to a JSON file with program metadata.
    """
    overall_results = []

    with open(metadata_file) as file:
        metadata = json.load(file)

    try:
        for program in metadata["programs"]:
            name = program["name"]
            path = Path(program["path"])
            tests = program["tests"]

            program_result = {
                "program": name,
                "status": "passed",
                "stage_failed": "",
                "error": "",
                "tests": [],
            }

            print(f"Processing '{name}'")

            # Stage 1: Build C code with Bear
            if not run_stage(Stage.C_BUILD, "bear -- make", path, program_result):
                overall_results.append(program_result)
                continue

            # Stage 2: Transpile C to Rust
            if not run_stage(
                Stage.TRANSPILE,
                "c2rust transpile --emit-build-files compile_commands.json",
                path,
                program_result,
            ):
                overall_results.append(program_result)
                continue

            # Stage 3: Build transpiled Rust
            if not run_stage(
                Stage.RUST_BUILD,
                "cargo build --release",
                path,
                program_result,
            ):
                overall_results.append(program_result)
                continue

            # Stage 4–5: Link and run tests
            for test in tests:
                test_path = Path(test)
                test_name = f"c2rust_{test_path.stem}"
                test_result = {"name": test, "status": "passed"}

                # TODO:
                # Test C program on their own tests.
                # Test Rust program on the transpiled tests.

                # Link C test binary against Rust library
                if not run_stage(
                    Stage.RUST_LINK,
                    f"gcc -o {test_name} {test} -Isrc -Ltarget/release -lc2rust_out -ldl -lpthread -lm",
                    path,
                    test_result,
                ):
                    program_result.update(
                        status="failed", stage_failed=str(Stage.RUST_LINK)
                    )
                    program_result["tests"].append(test_result)
                    break

                # Execute linked test binary
                if not run_stage(
                    Stage.RUST_TEST,
                    f"./{test_name}",
                    path,
                    test_result,
                ):
                    program_result.update(
                        status="failed", stage_failed=str(Stage.RUST_TEST)
                    )
                    program_result["tests"].append(test_result)
                    break

                program_result["tests"].append(test_result)

            overall_results.append(program_result)

    except Exception as e:
        print(f"Unexpected error: {e}")

    finally:
        # Summary statistics
        total_programs = len(overall_results)
        programs_passed = sum(1 for r in overall_results if r["status"] == "passed")
        programs_failed = total_programs - programs_passed

        failed_at = {str(stage): 0 for stage in Stage}
        for program_result in overall_results:
            if program_result["status"] == "failed":
                stage = program_result["stage_failed"]
                failed_at[stage] = failed_at.get(stage, 0) + 1

        summary = {
            "total_programs": total_programs,
            "programs_passed": programs_passed,
            "programs_failed": programs_failed,
            **{f"failed_at_{stage}": count for stage, count in failed_at.items()},
        }

        with open("test_results.json", "w") as file:
            json.dump({"summary": summary, "overall_results": overall_results}, file)


if __name__ == "__main__":
    run_tests(METADATA_FILE)
