# Copyright 2025 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Parse JUnit XML test report, generate a markdown summary, and optionally post it to a PR."""

import os
import subprocess
import xml.etree.ElementTree as ET


def parse_report(xml_path: str, branches: dict[str, str], run_url: str) -> str:
    """Parse JUnit XML and return a markdown summary string."""
    try:
        tree = ET.parse(xml_path)
    except (FileNotFoundError, ET.ParseError):
        return (
            "**Cross-Repo Integration Test:** "
            "No test report generated. Tests may have failed to collect.\n"
        )

    root = tree.getroot()
    file_results: dict[str, dict] = {}
    total_passed = 0
    total_failed = 0
    total_errors = 0

    for tc in root.findall(".//testcase"):
        classname = tc.get("classname", "")
        name = tc.get("name", "")
        file_path = classname.replace(".", "/") + ".py"

        if file_path not in file_results:
            file_results[file_path] = {"passed": 0, "failed": 0, "errors": 0, "failures": []}

        failure = tc.find("failure")
        error = tc.find("error")

        if failure is not None:
            file_results[file_path]["failed"] += 1
            total_failed += 1
            msg = (failure.get("message") or "").split("\n")[0][:120]
            file_results[file_path]["failures"].append(f"`{name}`: {msg}")
        elif error is not None:
            file_results[file_path]["errors"] += 1
            total_errors += 1
            msg = (error.get("message") or "").split("\n")[0][:120]
            file_results[file_path]["failures"].append(f"`{name}`: {msg}")
        else:
            file_results[file_path]["passed"] += 1
            total_passed += 1

    status = "PASSED" if (total_failed + total_errors) == 0 else "FAILED"
    icon = "\u2705" if status == "PASSED" else "\u274c"

    lines = [f"## Cross-Repo Integration Test {icon} {status}\n"]

    branch_lines = [f"- **{repo}:** `{branch}`" for repo, branch in branches.items() if branch]
    if not branch_lines:
        branch_lines.append("- _No branch overrides (using release versions)_")
    lines.append("**Branches used:**")
    lines.extend(branch_lines)
    lines.append("")

    lines.append("| Total Passed | Total Failed | Total Errors |")
    lines.append("|:---:|:---:|:---:|")
    lines.append(f"| {total_passed} | {total_failed} | {total_errors} |")
    lines.append("")

    if total_failed + total_errors > 0:
        lines.append("### Failures by file\n")
        lines.append("| File | Passed | Failed | Errors |")
        lines.append("|------|:---:|:---:|:---:|")
        for fp, r in file_results.items():
            if r["failed"] + r["errors"] > 0:
                lines.append(f"| `{fp}` | {r['passed']} | {r['failed']} | {r['errors']} |")
        lines.append("")
        lines.append("<details><summary>Failure details</summary>\n")
        for fp, r in file_results.items():
            if r["failures"]:
                lines.append(f"**`{fp}`**")
                for f in r["failures"]:
                    lines.append(f"- {f}")
                lines.append("")
        lines.append("</details>")

    lines.append(f"\n[View full run]({run_url})")
    return "\n".join(lines)


def post_to_pr(summary: str, repo: str, pr_number: int, token: str):
    """Post or update a comment on a GitHub PR using the gh CLI."""
    marker = "<!-- cross-repo-integration-test -->"
    body = f"{marker}\n{summary}"

    result = subprocess.run(
        [
            "gh", "api",
            f"repos/{repo}/issues/{pr_number}/comments",
            "--jq", ".[].id",
        ],
        capture_output=True,
        text=True,
        env={**os.environ, "GH_TOKEN": token},
    )
    existing_comments = result.stdout.strip().splitlines() if result.returncode == 0 else []

    existing_id = None
    for comment_id in existing_comments:
        check = subprocess.run(
            [
                "gh", "api",
                f"repos/{repo}/issues/comments/{comment_id}",
                "--jq", ".body",
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "GH_TOKEN": token},
        )
        if check.returncode == 0 and marker in check.stdout:
            existing_id = comment_id
            break

    if existing_id:
        subprocess.run(
            [
                "gh", "api",
                "--method", "PATCH",
                f"repos/{repo}/issues/comments/{existing_id}",
                "-f", f"body={body}",
            ],
            env={**os.environ, "GH_TOKEN": token},
            check=True,
        )
        print(f"Updated existing comment {existing_id} on PR #{pr_number}")
    else:
        subprocess.run(
            [
                "gh", "api",
                "--method", "POST",
                f"repos/{repo}/issues/{pr_number}/comments",
                "-f", f"body={body}",
            ],
            env={**os.environ, "GH_TOKEN": token},
            check=True,
        )
        print(f"Posted new comment on PR #{pr_number}")


def main():
    xml_path = os.environ.get("REPORT_XML", "report.xml")
    run_url = (
        f"{os.environ['GITHUB_SERVER_URL']}/{os.environ['GITHUB_REPOSITORY']}"
        f"/actions/runs/{os.environ['GITHUB_RUN_ID']}"
    )

    branches = {
        "qBraid SDK": os.environ.get("QBRAID_BRANCH", ""),
        "qbraid-core": os.environ.get("QBRAID_CORE_BRANCH", ""),
        "pyqasm": os.environ.get("PYQASM_BRANCH", ""),
    }

    summary = parse_report(xml_path, branches, run_url)

    summary_file = os.environ.get("GITHUB_STEP_SUMMARY", "")
    if summary_file:
        with open(summary_file, "a") as f:
            f.write(summary)

    output_path = os.environ.get("SUMMARY_OUTPUT", "test-summary.md")
    with open(output_path, "w") as f:
        f.write(summary)

    print(summary)

    pr_number = os.environ.get("PR_NUMBER", "").strip()
    token = os.environ.get("GH_TOKEN", "").strip()
    repo = os.environ.get("GITHUB_REPOSITORY", "")

    if pr_number and token and repo:
        try:
            post_to_pr(summary, repo, int(pr_number), token)
        except (ValueError, subprocess.CalledProcessError) as e:
            print(f"Warning: Failed to post to PR: {e}")


if __name__ == "__main__":
    main()
