from __future__ import annotations

import os
import sys

HERE = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(HERE, ".."))

for path in (HERE, PROJECT_ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)
