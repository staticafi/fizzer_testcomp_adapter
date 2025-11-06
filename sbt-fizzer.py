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


def _execute(command_and_args, timeout_ = None, stdout_=None, stderr_=None):
    cmd = [x for x in command_and_args if len(x) > 0]
    # print("*** CALLING ***\n" + " ".join(cmd) + "\n************\n")
    return subprocess.run(cmd, timeout=timeout_, stdout=stdout_, stderr=stderr_)


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


def get_file_arg_of_option(options, option):
    idx = safe_index(options, option)
    if idx is None:
        raise Exception(f"Missing {option} option.")
    if idx + 1 >= len(options):
        raise Exception(f"Missing argument of the {option} option.")
    if not os.path.isfile(options[idx + 1]):
        raise Exception(f"Cannot access file {options[idx + 1]} given by the {option} option.")
    return idx, options[idx + 1]


def main():
    if "--version" in sys.argv:
        print("1.2.3")
        return

    options = sys.argv[1:]

    prp_idx, prp_path = get_file_arg_of_option(options, "--property")
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

    if _execute([ sys.executable, os.path.join(os.path.dirname(__file__), "fizzer", "fizzer.py") ] + options).returncode:
        raise Exception("Call to Fizzer has failed.")

if __name__ == "__main__":
    exit_code = 0
    try:
        main()
    except Exception as e:
        exit_code = 1
    exit(exit_code)
