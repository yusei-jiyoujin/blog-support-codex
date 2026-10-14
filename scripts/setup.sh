#!/usr/bin/env bash
set -euo pipefail

task_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
task_python="${BLOG_PYTHON:-python3}"
"$task_python" -c 'import sys; assert sys.version_info >= (3, 10), "Python 3.10+ is required"'
if [[ ! -x "$task_root/.venv/bin/python" ]]; then
  "$task_python" -m venv "$task_root/.venv"
fi
"$task_root/.venv/bin/python" -m pip install --disable-pip-version-check -r "$task_root/requirements.txt"
"$task_root/.venv/bin/python" "$task_root/scripts/doctor.py"
