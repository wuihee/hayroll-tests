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
    # Compile again with all compile-time flags and generated a fresh
    # compile_commands.json.
    all_flags = " ".join(program.compile_flags)
    compile_c_program(all_flags, program.path)

    output_dir = (Path(program.path) / "hayroll-out").mkdir(exist_ok=True)

    return run_command(
        f"{hayroll_path} compile_commands.json {output_dir}",
        program.path,
    )


def run_tests() -> list[ProgramResults]:
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

        transpile_results = run_transpile(program, "")

        program_status = Status(passed=is_c_test_passed and transpile_results.passed)
        program_results.append(
            ProgramResults(
                name=program.name,
                status=program_status,
                c_test_results=c_test_results,
                transpile_results=transpile_results,
            )
        )

    return program_results
