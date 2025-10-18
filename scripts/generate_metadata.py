import json
from pathlib import Path

DATASET_DIR = Path("CBench")


def get_test_files(dir: Path) -> list[str]:
    test_files: set[Path] = set()

    for subdir in ["test", "tests"]:
        test_dir = dir / subdir
        if test_dir.exists():
            test_files.update(test_dir.rglob("*.c"))

    test_files.update(dir.rglob("*test*.c"))

    return [file.as_posix() for file in test_files]


programs_metadata = []

for program_dir in DATASET_DIR.iterdir():
    test_files = get_test_files(program_dir)
    program_metadata = {
        "name": program_dir.stem,
        "path": program_dir.as_posix(),
        "tests": test_files,
    }
    programs_metadata.append(program_metadata)

with open("crust_metadata.json", "w") as file:
    json.dump({"programs": programs_metadata}, file, sort_keys=True)
