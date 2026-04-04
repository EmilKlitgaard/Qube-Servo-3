"""
Python/platform package.

Exports the abstract interface and both concrete implementations so
callers can simply write:

    from platform import QubeInterface, Physical, Virtual
"""

from .QubeInterface import QubeInterface
from .Physical import Physical
from .Virtual import Virtual

__all__ = ["QubeInterface", "Physical", "Virtual"]