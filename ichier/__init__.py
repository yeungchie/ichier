from . import release

__author__ = release.author
__email__ = release.email
__license__ = release.license
__version__ = release.version
__url__ = release.url
__copyright__ = release.copyright

from .node import Design, Module, Instance, Net, Terminal
from .parser import fromVerilog, fromVerilogCode, fromSpice, fromSpiceCode

__all__ = [
    "Design",
    "Module",
    "Instance",
    "Net",
    "Terminal",
    "fromVerilog",
    "fromVerilogCode",
    "fromSpice",
    "fromSpiceCode",
]
