# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint: skip-file

"""
Script to verify qBraid copyright file headers

"""
import os
import sys

# ANSI escape codes
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"

header = """# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.
"""

skip_files = [
    "qbraid/api/retry.py",
    "qbraid/transpiler/cirq_braket/convert_from_braket.py",
    "qbraid/transpiler/cirq_braket/convert_to_braket.py",
    "qbraid/transpiler/cirq_qasm/qasm_parser.py",
    "qbraid/transpiler/cirq_pyquil/quil_output.py",
    "qbraid/transpiler/cirq_pyquil/quil_input.py",
    "tests/transpiler/cirq_braket/test_from_braket.py",
    "tests/transpiler/cirq_braket/test_to_braket.py",
    "tests/transpiler/cirq_qasm/test_qasm_parser.py",
    "tests/transpiler/cirq_pyquil/test_quil_output.py",
    "tests/transpiler/cirq_pyquil/test_quil_input.py",
]

failed_headers = []
fixed_headers = []


def should_skip(file_path, content):
    if file_path in skip_files:
        return True

    if os.path.basename(file_path) == "__init__.py":
        return not content.strip()

    return False


def replace_or_add_header(file_path, fix=False):
    with open(file_path, "r", encoding="ISO-8859-1") as f:
        content = f.read()

    if content.startswith(header) or should_skip(file_path, content):
        return

    if not fix:
        failed_headers.append(file_path)
        return

    lines = content.splitlines()

    comment_lines = []
    first_skipped_line = None
    for index, line in enumerate(lines):
        if line.startswith("#"):
            comment_lines.append(line)
        else:
            first_skipped_line = index
            break

    new_content_lines = [header.rstrip("\r\n")] + lines[first_skipped_line:]
    new_content = "\n".join(new_content_lines) + "\n"

    with open(file_path, "w", encoding="ISO-8859-1") as f:
        f.write(new_content)

    fixed_headers.append(file_path)


def process_files_in_directory(directory, fix=False):
    count = 0
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                replace_or_add_header(file_path, fix)
                count += 1
    return count


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide at least one directory as a command-line argument.")
        sys.exit(1)

    script_directory = os.path.dirname(os.path.abspath(__file__))
    project_directory = os.path.abspath(os.path.join(script_directory, ".."))
    skip_files = [os.path.join(project_directory, file_path) for file_path in skip_files]

    fix = "--fix" in sys.argv
    directories = [arg for arg in sys.argv[1:] if arg != "--fix"]

    checked = 0
    for directory in directories:
        full_directory_path = os.path.join(project_directory, directory)
        if os.path.isdir(full_directory_path):
            checked += process_files_in_directory(full_directory_path, fix)
        else:
            failed_headers.append(full_directory_path)
            print(f"Directory not found: {full_directory_path}")

    if not fix:
        if failed_headers:
            for file in failed_headers:
                print(f"failed {os.path.relpath(file)}")
            num_failed = len(failed_headers)
            s1, s2 = ("", "s") if num_failed == 1 else ("s", "")
            sys.stderr.write(f"\n{num_failed} file header{s1} need{s2} updating.\n")
            sys.exit(1)
        else:
            print("All file header checks passed!")

    else:
        for file in fixed_headers:
            print(f"fixed {os.path.relpath(file)}")
        num_fixed = len(fixed_headers)
        num_ok = checked - num_fixed
        s_fixed = "" if num_fixed == 1 else "s"
        s_ok = "" if num_ok == 1 else "s"
        print("\nAll done! ✨ 🚀 ✨")
        print(f"{num_fixed} header{s_fixed} fixed, {num_ok} header{s_ok} left unchanged.")
