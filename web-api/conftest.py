from __future__ import annotations

import os
import sys

HERE = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(HERE, ".."))
TESTS_DIR = os.path.join(HERE, "tests")

for path in (PROJECT_ROOT, HERE, TESTS_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

os.environ.setdefault("FLASK_TESTING", "1")
