"""
Data models for Hayroll test runner.

This module defines the data structures used to represent test programs,
their execution results, and associated metadata throughout the testing pipeline.
"""

from dataclasses import dataclass


@dataclass
class ProgramMetadata:
    """
    Metadata for a single test program used to evaluate Hayroll.
    """

    name: str
    path: str
    tests: list[str]
    compile_flags: list[str]


@dataclass
class Status:
    passed: bool
    stdout: str = ""
    stderr: str = ""


@dataclass
class CompileResult:
    """
    Results from compiling a program with specific flags.
    """

    status: Status
    compile_flag: str


@dataclass
class SingleTestResult:
    """
    Results from running a single test executable.
    """

    status: Status
    test_file: str


@dataclass
class TestResults:
    """
    Aggregated results for compilation and all tests for a specific compile flag.
    """

    status: Status
    compile_result: CompileResult
    test_results: list[SingleTestResult]


@dataclass
class ProgramResults:
    """
    Complete test results for a program through all pipeline stages.

    This represents the full lifecycle of testing a program: running the original
    C tests, transpiling to Rust, and running tests on the Rust version.
    """

    name: str
    status: Status
    c_test_results: list[TestResults]
    transpile_results: Status
    # rust_test_results: list[TestResults]
