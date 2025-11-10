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
    SingleTestResult,
    Status,
    TestResults,
)
from .preprocessing import get_compile_flag_combinations, get_test_programs


def compile_c_program(compile_flag: str, program_path: str) -> CompileResult:
    """
    Compile a C program using make with the specified compiler flags.

    Args:
        compile_flag: Compiler flag combination to use (e.g., "-O2 -Wall").
                      Can be empty string for default compilation.
        program_path: Path to the directory containing the program's Makefile.

    Returns:
        CompileResult containing the compilation status and any error messages.
    """
    print(compile_flag)
    subprocess.run(
        "make clean",
        cwd=program_path,
        capture_output=True,
        text=True,
        shell=True,
    )
    command_result = subprocess.run(
        f"bear -- make {compile_flag}",
        cwd=program_path,
        capture_output=True,
        text=True,
        shell=True,
    )
    status = Status.PASSED if command_result.returncode == 0 else Status.FAILED
    error = command_result.stderr
    return CompileResult(compile_flag=compile_flag, status=status, error=error)


def run_single_test(test_file: str, program_path: str) -> SingleTestResult:
    """
    Execute a single test executable and capture its results.

    Args:
        test_file: Name of the test executable to run.
        program_path: Path to the directory containing the test executable.

    Returns:
        SingleTestResult containing the test status and any error output.
    """
    test_file_path = Path(test_file)
    test_name = test_file_path.stem
    command_result = subprocess.run(
        [f"./{test_name}"],
        cwd=program_path,
        capture_output=True,
        text=True,
        shell=True,
    )
    status = Status.PASSED if command_result.returncode == 0 else Status.FAILED
    error = command_result.stderr
    return SingleTestResult(test_file=test_file, status=status, error=error)


def run_c_tests(program: ProgramMetadata) -> list[TestResults]:
    """
    Compile and run tests for a C program for each compile-flag combination.

    Args:
        program: Metadata for the program to test, including compile flags
                and test executables.

    Returns:
        List of TestResults, one for each compile flag combination.
        Test results will be empty if compilation failed for that combination.
    """
    c_test_results = []
    compile_flag_combinations = get_compile_flag_combinations(program.compile_flags)

    for compile_flag in compile_flag_combinations:
        compile_result = compile_c_program(compile_flag, program.path)

        test_results = []
        if compile_result.status == Status.PASSED:
            for test_file in program.tests:
                test_result = run_single_test(test_file, program.path)
                test_results.append(test_result)

        c_test_results.append(
            TestResults(
                compile_result=compile_result,
                test_results=test_results,
            )
        )

    return c_test_results


def run_tests() -> list[TestResults]:
    """
    Run C tests for all test programs.

    Returns:
        A list of test results for each program's compile flag combinations.
    """
    test_programs = get_test_programs()
    all_results = []

    for program in test_programs:
        c_test_results = run_c_tests(program)
        all_results.extend(c_test_results)

    print(all_results)
    return all_results
