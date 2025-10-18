import subprocess
import json
from pathlib import Path

METADATA_FILE = Path("crust_metadata.json")


def run(command: str, path: str) -> tuple[bool, str, str]:
    """Run a shell command in a given directory and return success, stdout, stderr."""
    result = subprocess.run(
        command, cwd=path, capture_output=True, text=True, shell=True
    )
    return result.returncode == 0, result.stdout, result.stderr


with open(METADATA_FILE) as file:
    metadata = json.load(file)

results = []

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

    # Make
    success, _, error = run("bear -- make", path)
    if not success:
        result.update(status="failed", stage_failed="make", error=error)
        results.append(result)
        continue

    # Transpile
    success, _, error = run(
        "c2rust transpile --emit-build-files compile_commands.json", path
    )
    if not success:
        result.update(status="failed", stage_failed="transpile", error=error)
        results.append(result)
        continue

    # Build
    success, _, error = run("cargo build --release", path)
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
        success, _, error = run(
            f"gcc -o {test_name} {test} -Isrc -Ltarget/release -lc2rust_out -ldl -lpthread -lm",
            path,
        )
        if not success:
            result.update(status="failed", stage_failed="link", error=error)
            test_result.update(status="failed", error=error)
            result["tests"].append(test_result)
            break

        # Run Test
        success, _, error = run(f"./{test_name}", path)
        if not success:
            result.update(status="failed", stage_failed="test", error=error)
            test_result.update(status="failed", error=error)
            result["tests"].append(test_result)
            break

        result["tests"].append(test_result)

    results.append(result)

# Write results to file
with open("test_results.json", "w") as file:
    json.dump({"programs": results}, file, indent=2)
