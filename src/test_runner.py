"""
Test runner for Hayroll C-to-Rust transpiler validation.

This module provides functionality to compile and test C programs with various
compiler flag combinations. It handles the compilation stage and test execution,
tracking results for later analysis.
"""

import subprocess
from pathlib import Path

from .models import (
    CompileResult,
    ProgramMetadata,
    ProgramResults,
    SingleTestResult,
    Status,
    TestResults,
)
from .preprocessing import get_compile_flag_combinations, get_test_programs


def run_command(command: str, program_path: str) -> Status:
    """
    Helper method for running a command.
    """
    try:
        command_result = subprocess.run(
            command,
            cwd=program_path,
            capture_output=True,
            text=True,
            shell=True,
        )
        passed = command_result.returncode == 0
        return Status(
            passed=passed,
            stdout=command_result.stdout,
            stderr=command_result.stderr,
        )
    except subprocess.TimeoutExpired:
        return Status(passed=False, stderr="Command timed out")
    except Exception as e:
        return Status(passed=False, stderr=f"Command failed: {str(e)}")


def compile_c_program(compile_flag: str, program_path: str) -> CompileResult:
    """
    Compile a C program using make with the specified compiler flags.
    """
    run_command("make clean", program_path)
    status = run_command(f'bear -- make DEFINES="{compile_flag}"', program_path)
    return CompileResult(
        status=status,
        compile_flag=compile_flag,
    )


def run_single_test(test_file: str, program_path: str) -> SingleTestResult:
    """
    Execute a single test executable and capture its results.
    """
    test_file_path = Path(test_file)
    test_name = test_file_path.stem
    status = run_command(f"./{test_name}", program_path)
    return SingleTestResult(
        status=status,
        test_file=test_file,
    )


def run_c_tests(program: ProgramMetadata) -> list[TestResults]:
    """
    Compile and run tests for a C program for each compile-flag combination.
    """
    c_test_results = []
    compile_flag_combinations = get_compile_flag_combinations(program.compile_flags)

    for compile_flag in compile_flag_combinations:
        compile_result = compile_c_program(compile_flag, program.path)

        test_results = []
        if compile_result.status.passed:
            for test_file in program.tests:
                test_result = run_single_test(test_file, program.path)
                test_results.append(test_result)

        test_status = all(test_result.status.passed for test_result in test_results)
        is_tests_passed = compile_result.status.passed and test_status
        c_test_status = Status(passed=compile_result.status.passed and is_tests_passed)

        c_test_results.append(
            TestResults(
                status=c_test_status,
                compile_result=compile_result,
                test_results=test_results,
            )
        )

    return c_test_results


def run_transpile(program: ProgramMetadata, hayroll_path: str) -> Status:
    """
    Transpile a C program to Rust.
    """
    # Compile with all compile-time flags and generated a fresh
    # `compile_commands.json`.
    all_flags = " ".join(program.compile_flags)
    compile_c_program(all_flags, program.path)

    return run_command(
        f"{hayroll_path} compile_commands.json hayroll-out",
        program.path,
    )


def compile_rust_program(compile_flag: str, program_path: str) -> Status:
    """
    Compile the transpiled Rust program using Cargo with specific features.
    """
    features = [
        flag.replace("-D", "") for flag in compile_flag.split() if flag.startswith("-D")
    ]
    if features:
        features_str = ",".join(features)
        cargo_command = f"cargo build --release --features {features_str}"
    else:
        cargo_command = "cargo build --release"

    return run_command(cargo_command, program_path)


def link_and_run_rust_test(test_file: str, program_path: str) -> SingleTestResult:
    """
    Link a C test file against the transpiled Rust library and run the test.
    """
    test_file_path = Path(test_file)
    test_name = test_file_path.stem
    rust_test_name = f"rust_{test_name}"

    link_command = (
        f"gcc -o {rust_test_name} {test_file} -Isrc "
        f"-Ltarget/release -lc2rust_out -ldl -lpthread -lm"
    )
    link_status = run_command(link_command, program_path)

    if not link_status.passed:
        return SingleTestResult(
            status=Status(
                passed=False,
                stdout=link_status.stdout,
                stderr=f"Link failed: {link_status.stderr}",
            ),
            test_file=test_file,
        )

    test_status = run_command(f"./{rust_test_name}", program_path)

    return SingleTestResult(
        status=test_status,
        test_file=test_file,
    )


def run_rust_tests(program: ProgramMetadata) -> list[TestResults]:
    """
    Compile and run tests for the transpiled Rust program for each compile-flag combination.
    """
    rust_test_results = []
    compile_flag_combinations = get_compile_flag_combinations(program.compile_flags)

    for compile_flag in compile_flag_combinations:
        compile_result = CompileResult(
            status=compile_rust_program(compile_flag, program.path),
            compile_flag=compile_flag,
        )

        test_results = []
        if compile_result.status.passed:
            for test_file in program.tests:
                test_result = link_and_run_rust_test(test_file, program.path)
                test_results.append(test_result)

        test_status = all(test_result.status.passed for test_result in test_results)
        overall_status = Status(passed=compile_result.status.passed and test_status)

        rust_test_results.append(
            TestResults(
                status=overall_status,
                compile_result=compile_result,
                test_results=test_results,
            )
        )

    return rust_test_results


def run_tests(hayroll_path: str) -> list[ProgramResults]:
    """
    Run the entire C2Rust evaluation on all test programs.
    """
    test_programs = get_test_programs()
    program_results = []

    for program in test_programs:
        c_test_results = run_c_tests(program)
        is_c_test_passed = all(
            test_result.status.passed for test_result in c_test_results
        )

        transpile_results = run_transpile(program, hayroll_path)
        print(transpile_results)

        rust_test_results = run_rust_tests(program)

        program_status = Status(passed=is_c_test_passed and transpile_results.passed)
        program_results.append(
            ProgramResults(
                name=program.name,
                status=program_status,
                c_test_results=c_test_results,
                transpile_results=transpile_results,
                rust_test_results=rust_test_results,
            )
        )

    return program_results
