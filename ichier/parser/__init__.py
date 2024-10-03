from .spice import fromFile as fromSpice
from .verilog import fromFile as fromVerilog

__all__ = [
    "fromSpice",
    "fromVerilog",
]
