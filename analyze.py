import json

total_tests = 0
tests_passed = 0

with open("benchmark_summary.json") as file:
    results = json.load(file)

for program, test_results in results.items():
    if test_results["status"] == "passed":
        tests_passed += 1
    total_tests += 1

print(f"Tests Passed: {tests_passed}/{total_tests}")
