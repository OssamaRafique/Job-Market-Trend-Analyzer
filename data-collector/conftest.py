"""Make the service folder and the project root importable during tests.

Allows ``import muse_client`` (from the service) and ``from shared.db import ...``
(from the project root) to resolve without needing PYTHONPATH gymnastics when
running ``pytest`` inside this folder.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(HERE, ".."))

for path in (HERE, PROJECT_ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)
