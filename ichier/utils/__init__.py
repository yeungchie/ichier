from typing import Dict, Iterable, List, Optional, Union

from . import name_parse
from .log import logger

__all__ = [
    "logger",
    "flattenMemName",
    "expandTermNetPairs",
]


def flattenMemName(name: str) -> List[str]:
    return name_parse.parse(name)


def expandTermNetPairs(
    term: Union[str, Iterable[str]],
    net: Union[str, Iterable[str]],
    count: Optional[int] = None,
) -> Dict[str, str]:
    pairs = {}
    if isinstance(term, str) and isinstance(net, str):
        if count is None:
            raise ValueError("count must be specified")
        for i in range(count - 1, -1, -1):
            pairs[f"{term}[{i}]"] = f"{net}[{i}]"
    elif isinstance(term, str) and isinstance(net, Iterable):
        nets = list(net)
        for i, net in zip(range(len(nets) - 1, -1, -1), nets):
            if "<" in net:
                ls, rs = "<", ">"
            else:
                ls, rs = "[", "]"
            pairs[f"{term}{ls}{i}{rs}"] = net
    elif isinstance(term, Iterable) and isinstance(net, str):
        terms = list(term)
        for term, i in zip(terms, range(len(terms) - 1, -1, -1)):
            if "<" in term:
                ls, rs = "<", ">"
            else:
                ls, rs = "[", "]"
            pairs[term] = f"{net}{ls}{i}{rs}"
    elif isinstance(term, Iterable) and isinstance(net, Iterable):
        terms = list(term)
        nets = list(net)
        if len(terms) != len(nets):
            raise ValueError("term and net must have the same length")
        for term, net in zip(terms, nets):
            pairs[term] = net
    else:
        raise TypeError("term and net must be either str or iterable")
    return pairs
