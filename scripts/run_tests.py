import json
import subprocess
from pathlib import Path

METADATA_FILE = Path("crust_metadata.json")

results = []


def run(command: str, path: str) -> tuple[bool, str]:
    """
    Helper function to run a shell command.

    Args:
        command (str): The command to run.
        path (str): The path to run the command in.

    Returns:
        tuple[bool, str]: If the command succeeded, we return `(True, "")`.
                          Otherwise, `(False, error)`, where `error` is the
                          output to stderr.
    """
    result = subprocess.run(
        command, cwd=path, capture_output=True, text=True, shell=True
    )
    return result.returncode == 0, result.stderr


with open(METADATA_FILE) as file:
    metadata = json.load(file)

try:
    for program in metadata["programs"]:
        name = program["name"]
        path = program["path"]
        tests = program["tests"]

        result = {
            "program": name,
            "status": "passed",
            "stage_failed": "",
            "error": "",
            "tests": [],
        }

        print(f"Processing '{name}'")

        # Make
        success, error = run("bear -- make", path)
        if not success:
            result.update(status="failed", stage_failed="make", error=error)
            results.append(result)
            continue

        # Transpile
        success, error = run(
            "c2rust transpile --emit-build-files compile_commands.json", path
        )
        if not success:
            result.update(
                status="failed", stage_failed="transpile", error=error
            )
            results.append(result)
            continue

        # Build
        success, error = run("cargo build --release", path)
        if not success:
            result.update(status="failed", stage_failed="build", error=error)
            results.append(result)
            continue

        # Link and run each test
        for test in tests:
            test_path = Path(test)
            test_name = f"c2rust_{test_path.stem}"
            test_result = {"name": test, "status": "passed"}

            # Link
            success, error = run(
                f"gcc -o {test_name} {test} -Isrc -Ltarget/release -lc2rust_out -ldl -lpthread -lm",
                path,
            )
            if not success:
                result.update(status="failed", stage_failed="link")
                test_result.update(status="failed", error=error)
                result["tests"].append(test_result)
                break

            # Run Test
            success, error = run(f"./{test_name}", path)
            if not success:
                result.update(status="failed", stage_failed="test")
                test_result.update(status="failed", error=error)
                result["tests"].append(test_result)
                break

            result["tests"].append(test_result)

        results.append(result)

except Exception as e:
    print(e)

finally:
    # Overall stats
    total_tests = 0
    passed = 0
    failed = 0

    # Stages
    failed_at_make = 0
    failed_at_transpile = 0
    failed_at_build = 0
    failed_at_link = 0
    failed_at_test = 0

    for result in results:
        if result["status"] == "failed":
            failed += 1
            match result["stage_failed"]:
                case "make":
                    failed_at_make += 1
                case "transpile":
                    failed_at_transpile += 1
                case "build":
                    failed_at_build += 1
                case "link":
                    failed_at_link += 1
                case "test":
                    failed_at_test += 1
        else:
            passed += 1
        total_tests += 1

    with open("test_results.json", "w") as file:
        json.dump(
            {
                "results": {
                    "total_tests": total_tests,
                    "passed": passed,
                    "failed": failed,
                    "failed_at_make": failed_at_make,
                    "failed_at_transpile": failed_at_transpile,
                    "failed_at_build": failed_at_build,
                    "failed_at_link": failed_at_link,
                    "failed_at_test": failed_at_test,
                },
                "programs": results,
            },
            file,
        )
