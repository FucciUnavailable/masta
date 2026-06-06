"""Tools the agent can call. Coaches declare which tools they're allowed to use.

The :class:`~masta.tools.base.Tool` interface and registry are live; concrete tools
(``web_search``, ``notify``) are stubs in the MVP.
"""

from __future__ import annotations

from masta.tools.base import Tool, ToolRegistry, registry

__all__ = ["Tool", "ToolRegistry", "registry"]
