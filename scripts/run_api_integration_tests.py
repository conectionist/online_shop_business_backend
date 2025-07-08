# scripts/run_api_integration_tests.py
import os
import sys
import json
import pytest
from datetime import datetime
from typing import Tuple, Dict, Any

TEST_DIR = "/app/tests/integration"
JSON_REPORT_PATH = "/tmp/pytest_report.json"

def run_tests() -> Tuple[int, Dict[str, Any]]:
    """
    Run pytest, parse its report, and return the exit code and results.
    """
    # Run pytest and generate a JSON report
    exit_code = pytest.main([
        TEST_DIR,
        "--json-report",
        f"--json-report-file={JSON_REPORT_PATH}"
    ])

    # Check if the report was created
    if not os.path.exists(JSON_REPORT_PATH):
        print(f"Error: Pytest JSON report not found at {JSON_REPORT_PATH}", file=sys.stderr)
        return 1, {}

    # Load the pytest report
    with open(JSON_REPORT_PATH) as f:
        report = json.load(f)

    # Process the report into the desired format
    final_results = {
        "timestamp": report.get("created"),
        "total_tests": report.get("summary", {}).get("total", 0),
        "passed": report.get("summary", {}).get("passed", 0),
        "failed": report.get("summary", {}).get("failed", 0),
        "results": {}
    }

    # Group test results by module
    for test in report.get("tests", []):
        module_name = test["nodeid"].split("::")[0].replace("tests/integration/", "").replace(".py", "")
        if module_name not in final_results["results"]:
            final_results["results"][module_name] = {
                "status": "passed",
                "tests_run": 0,
                "failures": 0
            }
        
        final_results["results"][module_name]["tests_run"] += 1
        if test["outcome"] == "failed":
            final_results["results"][module_name]["status"] = "failed"
            final_results["results"][module_name]["failures"] += 1

    return exit_code, final_results

if __name__ == "__main__":
    exit_code, test_results = run_tests()
    
    if test_results:
        # Ensure the report directory exists
        report_dir = "/test-reports/integration"
        os.makedirs(report_dir, exist_ok=True)
        
        # Write the final JSON report
        final_report_path = os.path.join(report_dir, "integration_test_report.json")
        with open(final_report_path, "w") as f:
            json.dump(test_results, f, indent=4)
            
        print(f"\n{'='*50}")
        print("Integration test run complete.")
        print(f"Report saved to {final_report_path}")
    
    sys.exit(exit_code)
