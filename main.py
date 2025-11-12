import json
from dataclasses import asdict

from src import run_tests

test_results = run_tests(
    "/mnt/c/Users/wuihee/Desktop/programming/research/Hayroll/hayroll"
)
with open("test_results.json", "w") as file:
    results_asdict = [asdict(result) for result in test_results]
    json.dump(results_asdict, file, indent=2)
