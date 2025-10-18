import json
from pathlib import Path


def find_test_files(project_path):
    """Find all test .c files in a project directory."""
    test_files = []
    project_dir = Path(project_path)

    # First look for files in test/tests directories
    test_dir_patterns = [
        "tests/**/*.c",
        "**/tests/**/*.c",
        "test/**/*.c",
        "**/test/**/*.c",
    ]

    # Then look for test-named files
    test_name_patterns = ["**/test*.c", "**/*test*.c"]

    seen_files = set()

    # Process test directory patterns first (higher priority)
    for pattern in test_dir_patterns:
        for file in project_dir.glob(pattern):
            rel_path = file.relative_to(project_dir)
            rel_path_str = str(rel_path).replace("\\", "/")

            if rel_path_str not in seen_files:
                test_files.append(rel_path_str)
                seen_files.add(rel_path_str)

    # Process test name patterns
    for pattern in test_name_patterns:
        for file in project_dir.glob(pattern):
            rel_path = file.relative_to(project_dir)
            rel_path_str = str(rel_path).replace("\\", "/")

            if rel_path_str not in seen_files:
                test_files.append(rel_path_str)
                seen_files.add(rel_path_str)

    # Also check for test.c in root
    root_test = project_dir / "test.c"
    if root_test.exists():
        rel_path_str = "test.c"
        if rel_path_str not in seen_files:
            test_files.append(rel_path_str)

    return sorted(test_files)


def generate_metadata():
    """Generate complete metadata.json for all CBench projects."""
    cbench_dir = Path("CBench")
    programs = []

    # Get all directories in CBench
    for project_dir in sorted(cbench_dir.iterdir()):
        if project_dir.is_dir():
            project_name = project_dir.name
            test_files = find_test_files(project_dir)

            program_entry = {
                "name": project_name,
                "path": project_name,
                "test_files": test_files,
            }

            programs.append(program_entry)
            print(f"Processed {project_name}: {len(test_files)} test files")

    metadata = {"programs": programs}

    # Write to metadata.json
    with open("metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\nTotal projects: {len(programs)}")
    print("Metadata.json has been updated successfully!")


if __name__ == "__main__":
    generate_metadata()
