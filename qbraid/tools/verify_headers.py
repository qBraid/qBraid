# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
# 
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Script to verify qBraid copyright file headers

"""
import os
import re

header = '''# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
# 
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.
'''

companies = [
    "Unitary Fund",
    "IBM",
    "The Cirq Developers",
]

def header_exists(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    return content.startswith(header)

def starts_with_skip_header(content):
    lines = content.splitlines()
    if len(lines) < 2:
        return False

    first_line = lines[0]
    second_line = lines[1]
    qbraid_copyright = "# Copyright (C) 2023 qBraid"
    company_copyright = re.compile(r"# Copyright \(C\) \[(.+)\]")

    match = company_copyright.match(second_line)
    if match and first_line == qbraid_copyright:
        company = match.group(1)
        return company in companies

    return False

def replace_or_add_header(file_path):
    with open(file_path, 'r') as f:
        content = f.read()

    if header_exists(file_path) or starts_with_skip_header(content):
        return

    lines = content.splitlines()

    comment_lines = []
    for line in lines:
        if line.startswith("#") or not line.strip():
            comment_lines.append(line)
        else:
            break

    new_content_lines = [header.rstrip('\r\n')] + lines[len(comment_lines):]
    new_content = '\n'.join(new_content_lines)

    with open(file_path, 'w') as f:
        f.write(new_content)

def process_files_in_directory(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                replace_or_add_header(file_path)

if __name__ == '__main__':
    script_directory = os.path.dirname(os.path.abspath(__file__))
    project_directory = os.path.abspath(os.path.join(script_directory, '..', '..'))
    process_files_in_directory(project_directory)
    print("Header added or replaced in all .py files in the specified directory and sub-directories, if applicable.")

