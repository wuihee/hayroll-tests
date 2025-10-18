import json

total_tests = 0
tests_passed = 0
make_failed = 0
transpile_failed = 0
rust_build_failed = 0
link_failed = 0
test_failed = 0

with open("benchmark_summary.json") as file:
    results = json.load(file)

for program, test_results in results.items():
    if test_results["status"] == "passed":
        tests_passed += 1
    else:
        failed_stage = test_results["failed_stage"]
        if failed_stage == "make":
            make_failed += 1
        elif failed_stage == "transpile":
            transpile_failed += 1
        elif failed_stage == "rust_build":
            rust_build_failed += 1
        elif failed_stage == "link":
            link_failed += 1
        elif failed_stage == "test":
            test_failed += 1
    total_tests += 1

print(f"Tests Passed: {tests_passed}/{total_tests}")
print(f"Make Failed: {make_failed}")
print(f"Transpile Failed: {transpile_failed}")
print(f"Rust Build Failed: {rust_build_failed}")
print(f"Link Failed: {link_failed}")
print(f"Test Failed: {test_failed}")
