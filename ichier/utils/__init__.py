from typing import Dict, Iterable, Optional, Union, overload

from .name_parse import bitInfoSplit, parse as nameparse

__all__ = [
    "bitInfoSplit",
    "flattenSequence",
    "parseMemName",
    "expandTermNetPairs",
]


@overload
def flattenSequence(data: list) -> list: ...
@overload
def flattenSequence(data: tuple) -> tuple: ...
def flattenSequence(data):
    if not isinstance(data, (list, tuple)):
        raise TypeError(f"data must be a list or tuple - {type(data)}")
    seq = type(data)
    result = []
    for item in data:
        if isinstance(item, (list, tuple)):
            result.extend(flattenSequence(item))
        else:
            result.append(item)
    return seq(result)


def parseMemName(name: str, flatten: bool = False) -> Union[str, list, tuple]:
    result = nameparse(name)
    if flatten:
        result = flattenSequence(result)
    return result


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
        nets = list(map(str, net))
        for i, net in zip(range(len(nets) - 1, -1, -1), nets):
            if "<" in net:
                ls, rs = "<", ">"
            else:
                ls, rs = "[", "]"
            pairs[f"{term}{ls}{i}{rs}"] = net
    elif isinstance(term, Iterable) and isinstance(net, str):
        terms = list(map(str, term))
        for term, i in zip(terms, range(len(terms) - 1, -1, -1)):
            if "<" in term:
                ls, rs = "<", ">"
            else:
                ls, rs = "[", "]"
            pairs[term] = f"{net}{ls}{i}{rs}"
    elif isinstance(term, Iterable) and isinstance(net, Iterable):
        terms = list(map(str, term))
        nets = list(map(str, net))
        if len(terms) != len(nets):
            raise ValueError("term and net must have the same length")
        for term, net in zip(terms, nets):
            pairs[term] = net
    else:
        raise TypeError("term and net must be either str or iterable")
    return pairs
