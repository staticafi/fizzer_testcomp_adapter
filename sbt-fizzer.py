#!/usr/bin/env python3
import subprocess
import sys
import os
import time
import shutil
from datetime import datetime


testcomp_testsuite_metadata = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<!DOCTYPE test-metadata PUBLIC "+//IDN sosy-lab.org//DTD test-format test-metadata 1.1//EN" "https://sosy-lab.org/test-format/test-metadata-1.1.dtd">
<test-metadata>
  <sourcecodelang>C</sourcecodelang>
  <producer>fizzer</producer>
  <specification>%%SPECIFICATION%%</specification>
  <programfile>%%PROGRAM_FILE%%</programfile>
  <programhash>null</programhash>
  <entryfunction>main</entryfunction>
  <architecture>%%ARCHITECTURE%%</architecture>
  <creationtime>%%CREATIONTIME%%</creationtime>
</test-metadata>
"""
testcomp_property_coverage_branches = "COVER( init(main()), FQL(COVER EDGES(@DECISIONEDGE)) )"
testcomp_property_coverage_error_call = "COVER( init(main()), FQL(COVER EDGES(@CALL(reach_error))) )"


def safe_index(lst, item, default=None):
    try:
        return lst.index(item)
    except ValueError:
        return default


def generate_testcomp_metadata_xml(input_file, output_dir, use_m32, property):
    test_suite_dir = os.path.join(output_dir, "test-suite")
    os.makedirs(test_suite_dir, exist_ok=True)
    content = testcomp_testsuite_metadata.replace(
        "%%SPECIFICATION%%", property
        ).replace(
        "%%PROGRAM_FILE%%", os.path.basename(input_file)
        ).replace(
        "%%ARCHITECTURE%%", "32" if use_m32 is True else "64"
        ).replace(
        "%%CREATIONTIME%%", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    with open(os.path.join(test_suite_dir, "metadata.xml"), "w") as f:
        f.write(content)


def get_file_arg_of_option(options, option, default=None):
    idx = safe_index(options, option)
    if idx is None:
        if default is None:
            raise Exception(f"Missing {option} option.")
        return -1, default
    if idx + 1 >= len(options):
        raise Exception(f"Missing argument of the {option} option.")
    if not os.path.isfile(options[idx + 1]):
        raise Exception(f"Cannot access file {options[idx + 1]} given by the {option} option.")
    return idx, options[idx + 1]


def determine_result(log):
    RESULT_DONE = "done"
    RESULT_UNKNOWN = "unknown"
    # RESULT_TIMEOUT = "TIMEOUT"
    RESULT_ERROR = "ERROR"

    if not log:
        return RESULT_UNKNOWN

    termination_type = None
    termination_reason = None
    for line in log.splitlines():
        line = line.strip()
        if termination_type is None and "termination_type" in line:
            termination_type = line.split(": ")[1].split('"')[1]
        elif termination_reason is None and "termination_reason" in line:
            termination_reason = line.split(": ")[1].split('"')[1]

    # Now we are ready to compute the result string.

    if termination_type not in [ "NORMAL", "SERVER_INTERNAL_ERROR" ]:
        result_code = RESULT_ERROR
    elif termination_type != "NORMAL":
        result_code = RESULT_UNKNOWN
    elif termination_reason in [ "ALL_REACHABLE_BRANCHINGS_COVERED", "FUZZING_STRATEGY_DEPLETED", "TIME_BUDGET_DEPLETED", "EXECUTIONS_BUDGET_DEPLETED" ]:
        result_code = RESULT_DONE
    else:
        result_code = RESULT_UNKNOWN

    return result_code + " (" + str(termination_type) + "," + str(termination_reason) + ")"


def main():
    if "--version" in sys.argv:
        print("1.2.3")
        return

    options = sys.argv[1:]

    prp_idx, prp_path = get_file_arg_of_option(options, "--property", "COVER( init(main()), FQL(COVER EDGES(@DECISIONEDGE)) )")
    if prp_idx == -1:
        property = prp_path # In this case it is the actual property (not a path to the property file).
        options.append("--test_type")
        options.append("testcomp")
        print("WARNING: The option --property was not passed to the tool. Using the default property: " + property, flush=True)
    else:
        with open(prp_path, "r") as f:
            property = f.read().strip()
        options[prp_idx] = "--test_type"
        options[prp_idx + 1] = "testcomp"

    output_dir = os.path.abspath(os.getcwd())
    options.append("--output_dir")
    options.append(output_dir)

    os.makedirs(output_dir, exist_ok=True)
    generate_testcomp_metadata_xml(
        get_file_arg_of_option(options, "--input_file")[1],
        output_dir,
        "--m32" in options,
        property
        )

    result = subprocess.run(
        [ sys.executable, os.path.join(os.path.dirname(__file__), "fizzer", "fizzer.py") ] + options,
        capture_output=True,      # Captures stdout and stderr
        text=True                 # Decodes bytes to string (UTF-8 by default)
        )
    if result.returncode:
        raise Exception("Call to Fizzer has failed.")

    print("--- stdout ---"); print(result.stdout, flush=True)
    print("--- stderr ---"); print(result.stderr, flush=True)
    print("--- ExitCode ---"); print(result.returncode, flush=True)
    print("--- TestCompResult ---"); print(determine_result(result.stdout), flush=True)

if __name__ == "__main__":
    exit_code = 0
    try:
        main()
    except Exception as e:
        print(str(e), flush=True); print("--- TestCompResult ---"); print("ERROR", flush=True)
        exit_code = 1
    exit(exit_code)
