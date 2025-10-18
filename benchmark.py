import json
import os
import subprocess
from pathlib import Path


def run(command, cwd=None):
    try:
        result = subprocess.run(
            command, cwd=cwd, shell=True, capture_output=True, text=True
        )
        success = result.returncode == 0
        return success, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


results = {}

root_dir = Path.cwd()

with open("metadata.json") as file:
    benchmark_metadata = json.load(file)

for program in benchmark_metadata["programs"]:
    name = program["name"]
    path = program["path"]
    tests = program["test_files"]

    os.chdir(Path("CBench") / path)

    program_result = {
        "status": "passed",
        "failed_stage": None,
        "test_results": {},
    }

    success, out, err = run("bear -- make")
    if not success:
        program_result["status"] = "failed"
        program_result["failed_stage"] = "make"
        program_result["error"] = err
        results[name] = program_result
        os.chdir(root_dir)
        continue

    success, out, err = run(
        "c2rust transpile --emit-build-files compile_commands.json"
    )
    if not success:
        program_result["status"] = "failed"
        program_result["failed_stage"] = "transpile"
        program_result["error"] = err
        results[name] = program_result
        os.chdir(root_dir)
        continue

    success, out, err = run("cargo build --release")
    if not success:
        program_result["status"] = "failed"
        program_result["failed_stage"] = "rust_build"
        program_result["error"] = err
        results[name] = program_result
        os.chdir(root_dir)
        continue

    for test_file in tests:
        exe_name = Path(test_file).stem + "_exe"
        compile_cmd = f"gcc -o {exe_name} {test_file} -Isrc -Ltarget/release -lc2rust_out -ldl -lpthread -lm"
        success, out, err = run(compile_cmd)
        if not success:
            program_result["test_results"][test_file] = {
                "status": "link_failed",
                "error": err,
            }
            program_result["status"] = "failed"
            program_result["failed_stage"] = "link"
            continue

        success, out, err = run(f"./{exe_name}")
        if success:
            program_result["test_results"][test_file] = {"status": "passed"}
        else:
            program_result["test_results"][test_file] = {
                "status": "failed",
                "stdout": out,
                "stderr": err,
            }
            program_result["status"] = "failed"
            program_result["failed_stage"] = "test"

    results[name] = program_result
    os.chdir(root_dir)

with open("benchmark_summary.json", "w") as file:
    json.dump(results, file)

print("Finished")
