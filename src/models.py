"""
Data models for Hayroll test runner.

This module defines the data structures used to represent test programs,
their execution results, and associated metadata throughout the testing pipeline.
"""

from dataclasses import dataclass
from enum import Enum


@dataclass
class ProgramMetadata:
    """
    Metadata for a single test program used to evaluate Hayroll.

    Attributes:
        name: The name of the test program.
        path: The file system path to the program's directory.
        tests: List of test executable names to run.
        compile_flags: List of compiler flags to test in combination.
    """

    name: str
    path: str
    tests: list[str]
    compile_flags: list[str]


class Status(Enum):
    """
    Represents the pass/fail status of a test or compilation.

    Attributes:
        PASSED: The operation completed successfully.
        FAILED: The operation failed with errors.
    """

    PASSED = 1
    FAILED = 2


class Stage(Enum):
    """
    Represents the different stages in the Hayroll testing pipeline.

    Attributes:
        C_TEST: Running tests on the original C program.
        TRANSPILE: Transpiling C code to Rust using Hayroll.
        RUST_TEST: Running tests on the transpiled Rust code.
    """

    C_TEST = 1
    TRANSPILE = 2
    RUST_TEST = 3


@dataclass
class CompileResult:
    """
    Results from compiling a program with specific flags.

    Attributes:
        compile_flag: The compiler flag combination used for this compilation.
        status: Whether the compilation passed or failed.
        error: Error output from the compiler (stderr), if any.
    """

    compile_flag: str
    status: Status
    error: str


@dataclass
class SingleTestResult:
    """
    Results from running a single test executable.

    Attributes:
        test_file: The name of the test executable that was run.
        status: Whether the test passed or failed.
        error: Error output from the test (stderr), if any.
    """

    test_file: str
    status: Status
    error: str


@dataclass
class TestResults:
    """
    Aggregated results for compilation and all tests for a specific compile flag.

    Attributes:
        compile_result: The result of compiling with specific flags.
        test_results: Results from each individual test executable.
                      Empty if compilation failed.
    """

    compile_result: CompileResult
    test_results: list[SingleTestResult]


@dataclass
class ProgramResults:
    """
    Complete test results for a program through all pipeline stages.

    This represents the full lifecycle of testing a program: running the original
    C tests, transpiling to Rust, and running tests on the Rust version.

    Attributes:
        name: The name of the test program.
        status: Overall pass/fail status for the entire pipeline.
        stage_failed: The stage at which testing failed (if status is FAILED).
        c_test_results: Results from running C tests with all compile flag combinations.
        transpile_status: Whether transpilation from C to Rust succeeded.
        rust_test_results: Results from running Rust tests with all compile flag combinations.
                           Empty if transpilation failed.
    """

    name: str
    status: Status
    stage_failed: Stage
    c_test_results: list[TestResults]
    transpile_status: Status
    rust_test_results: list[TestResults]
