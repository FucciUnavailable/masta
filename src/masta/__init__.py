"""masta — an AI-provider-agnostic coaching 'sensei'.

See ARCHITECTURE.md for the layered design. The public surface most callers need:

    from masta.config import get_settings
    from masta.llm import get_provider
    from masta.coaches import load_coaches
"""

__version__ = "0.1.0"
