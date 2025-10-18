import json
from pathlib import Path

DATASET_DIR = Path("CBench")


def get_test_files(dir: Path) -> list[Path]:
    """
    Retrieve all test files in a directory.

    Assume that all test files are .c files that contain 'test' in their name
    or live inside a 'test' or 'tests' directory.

    Args:
        dir (Path): The path to the directory.

    Returns:
        list[Path]: The list of test files.
    """
    test_files: set[Path] = set()

    for subdir in ["test", "tests"]:
        test_dir = dir / subdir
        if test_dir.exists():
            test_files.update(test_dir.rglob("*.c"))

    test_files.update(dir.rglob("*test*.c"))

    return test_files


programs_metadata = []

for program_dir in DATASET_DIR.iterdir():
    if not program_dir.is_dir:
        continue

    test_files = [
        file.relative_to(program_dir).as_posix()
        for file in get_test_files(program_dir)
    ]
    program_metadata = {
        "name": program_dir.stem,
        "path": program_dir.as_posix(),
        "tests": test_files,
    }

    programs_metadata.append(program_metadata)

with open("crust_metadata.json", "w") as file:
    json.dump({"programs": programs_metadata}, file)
