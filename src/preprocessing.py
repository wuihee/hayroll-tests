"""
This module provides utilities for preparing input data used by the Hayroll
testing pipeline.
"""

import json

from .models import ProgramMetadata


def get_compile_flag_combinations(compile_flags: list[str]) -> list[str]:
    """
    Find all combinations of compile-time flags for a C test program.

    Args:
        compile_flags: A list of all possible compile-time flags.

    Returns:
        A list of all possible combinations of compile-time flags to use for
        compiling a C program.
    """
    compile_flag_combinations = []

    def recursive_update(i: int = 0, current_combination: list[str] = []):
        if i == len(compile_flags):
            compile_flag_combinations.append(current_combination)
        else:
            recursive_update(i + 1, current_combination)
            recursive_update(i + 1, current_combination + [compile_flags[i]])

    recursive_update()
    return [" ".join(compile_flag) for compile_flag in compile_flag_combinations]


def get_test_programs() -> list[ProgramMetadata]:
    """
    Parses `test_programs.json` to get information about test programs in the
    dataset.

    Returns:
        A list of information about test programs including their name, path,
        compile-time flags, and test files.
    """
    with open("test_programs.json") as file:
        test_programs_metadata = json.load(file)
        test_programs = test_programs_metadata["programs"]

    return [ProgramMetadata(**program) for program in test_programs]
