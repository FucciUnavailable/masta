"""HTTP API — the same coach engine and memory the CLI uses, exposed for the web frontend.

Optional: install with ``pip install 'masta[web]'`` and run ``masta serve``.
"""

from __future__ import annotations

from masta.api.app import create_app

__all__ = ["create_app"]
