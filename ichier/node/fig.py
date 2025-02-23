from __future__ import annotations
from typing import Any, Iterable, Iterator, Literal, Optional, Union
from uuid import uuid4, UUID
import re

from . import obj

__all__ = [
    "Fig",
    "Collection",
    "FigCollection",
    "OrderList",
]


class Fig:
    __name: Optional[str] = None
    __collection: Optional["FigCollection"] = None

    def __init__(self, name: Optional[str] = None) -> None:
        self.__uuid = uuid4()
        self.name = name

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name!r})"

    def __str__(self) -> str:
        return self.name

    @property
    def type(self) -> str:
        return self.__class__.__name__

    @property
    def uuid(self) -> UUID:
        return self.__uuid

    @property
    def name(self) -> str:
        if self.__name is None:
            self.__name = f"{self.type}_{self.uuid.hex:.8}"
        return self.__name

    @name.setter
    def name(self, value: Optional[str]) -> None:
        if value == self.name:
            return
        if value is None:
            self.__name = None
            return
        if not isinstance(value, str):
            raise TypeError(f"name must be a string - {value!r}")
        old = self.name
        self.__name = value
        if self.collection is not None:
            self.collection.rename(old, value)

    def _setName(self, value: str) -> None:
        self.__name = value

    @property
    def collection(self) -> Optional["FigCollection"]:
        return self.__collection

    def _setCollection(self, value: Optional["FigCollection"]) -> None:
        if value is not None and not isinstance(value, FigCollection):
            raise TypeError(f"value must be a FigCollection or None - {value!r}")
        self.__collection = value

    def getModule(self) -> Optional[obj.Module]:
        collection = self.collection
        if collection is None:
            return
        if isinstance(collection.parent, obj.Module):
            return collection.parent
        else:
            return None

    def getDesign(self) -> Optional[obj.Design]:
        collection = self.collection
        if collection is None:
            return
        if isinstance(collection.parent, obj.Module):
            return collection.parent.getDesign()
        elif isinstance(collection.parent, obj.Design):
            return collection.parent
        else:
            return None

    def dump(
        self,
        format: Literal["spice", "verilog"] = "spice",
        *,
        width_limit: int = 88,
    ) -> str:
        if format == "spice":
            return self.dumpToSpice(width_limit=width_limit)
        elif format == "verilog":
            return self.dumpToVerilog(width_limit=width_limit)
        else:
            raise ValueError(f"Unsupported format {format!r}")

    def dumpToSpice(self, *args, **kwargs) -> str:
        raise NotImplementedError(
            f"Dump to spice is disabled for the {self.__class__.__name__!r}."
            " Please try to dump the parent node instead."
        )

    def dumpToVerilog(self, *args, **kwargs) -> str:
        raise NotImplementedError(
            f"Dump to verilog is disabled for the {self.__class__.__name__!r}."
            " Please try to dump the parent node instead."
        )


class Collection(dict):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__()
        if args == (None,) and not kwargs:
            return
        self.update(*args, **kwargs)

    @property
    def type(self) -> str:
        return self.__class__.__name__

    def __repr__(self) -> str:
        return self.repr()

    def repr(self, prompt: Optional[str] = None) -> str:
        if prompt is None:
            prompt = f"{self.__class__.__name__}"
        s = prompt + ":"

        if not self:
            return s + " empty"

        kvp = [*self.items()]
        s += "\n"

        if len(self) <= 6:
            s += "\n".join(f"  {k} -> {v}" for k, v in kvp)
        else:
            s += "\n".join(f"  {k} -> {v}" for k, v in kvp[:4])
            s += "\n  ...\n"
            s += "\n".join(f"  {k} -> {v}" for k, v in kvp[-2:])
        return s

    def _keyChecker(self, key: str) -> None:
        if not isinstance(key, str):
            raise KeyError(f"key must be a string - {key!r}")

    def _valueChecker(self, value: Any) -> None:
        pass

    def _dict__setitem__(self, key: str, value) -> None:
        super().__setitem__(key, value)

    def __setitem__(self, key: str, value: Any) -> None:
        self._keyChecker(key)
        self._valueChecker(value)
        self._dict__setitem__(key, value)

    def __getitem__(self, key: Union[int, str]) -> Any:
        if isinstance(key, int):
            key = tuple(self.keys())[key]
        elif isinstance(key, str):
            pass
        else:
            raise KeyError(f"key must be an integer or a string - {key!r}")
        return super().__getitem__(key)

    def update(self, *args, **kwargs) -> None:
        tmp = dict(*args, **kwargs)
        for key, value in tmp.items():
            self._keyChecker(key)
            self._valueChecker(value)
        for key, value in tmp.items():
            self.__setitem__(key, value)

    def append(self, value: Any) -> None:
        self.__setitem__(str(value), value)

    def extend(self, value: Iterable[Any]) -> None:
        self.update({str(x): x for x in value})

    def remove(self, key: str) -> None:
        if key not in self:
            raise KeyError(f"key not found - {key!r}")
        self.__delitem__(key)

    def setdefault(self, *args, **kwargs) -> None:
        raise NotImplementedError(f"setdefault() is disabled for class {self.type!r}")

    def __or__(self, other: "Collection") -> "Collection":
        if not isinstance(other, Collection):
            raise TypeError(f"other must be a Collection - {other!r}")
        result = Collection()
        result.update(self)
        result.update(other)
        return result

    def __ror__(self, other: "Collection") -> "Collection":
        if not isinstance(other, Collection):
            raise TypeError(f"other must be a Collection - {other!r}")
        result = Collection()
        result.update(other)
        result.update(self)
        return result

    def __ior__(self, other: dict) -> "Collection":
        self.update(other)
        return self

    def find(
        self,
        name: str,
        ignorecase: bool = False,
        dict_result: bool = False,
        target: Literal["key", "value"] = "key",
    ) -> Union[tuple, dict]:
        if target not in ("key", "value"):
            raise ValueError(f"target must be 'key' or 'value' - {target!r}")
        result = {}
        pattern = re.compile(name, flags=re.IGNORECASE if ignorecase else 0)
        for key, value in self.items():
            if target == "key":
                s = key
            elif target == "value":
                s = str(value)
            if pattern.fullmatch(s):
                result[key] = value
        if dict_result:
            return result
        else:
            return tuple(result.values())


class FigCollection(Collection):
    def __init__(
        self,
        parent: Union[obj.Module, obj.Design],
        figs: Iterable[Fig] = (),
    ) -> None:
        if not isinstance(parent, (obj.Module, obj.Design)):
            raise TypeError(f"parent must be a Module or Design - {parent!r}")
        if isinstance(figs, str):
            raise TypeError(f"figs must be an iterable of Fig - {figs!r}")
        super().__init__()
        self.__parent = parent
        self.extend(figs)

    def __repr__(self) -> str:
        s = f"{self.__class__.__name__}: {len(self)} figs"
        if not self:
            pass
        elif len(self) <= 6:
            s += f"\n{tuple(self.values())!r}"
        else:
            queue = [repr(x) for x in self.values()]
            s += "\n(" + ",\n ".join(queue[:4] + ["..."] + queue[-2:]) + ")"
        return s

    @property
    def parent(self) -> Union[obj.Module, obj.Design]:
        return self.__parent

    @property
    def order(self) -> tuple:
        return tuple(self.keys())

    @property
    def figs(self) -> tuple:
        return tuple(self.values())

    def _valueChecker(self, value: Fig) -> None:
        if not isinstance(value, Fig):
            raise TypeError(f"value must be a Fig object - {value!r}")

    def __setitem__(self, key: str, fig: Fig) -> None:
        self._keyChecker(key)
        self._valueChecker(fig)
        if key in self:
            del self[key]
        fig._setCollection(self)
        super()._dict__setitem__(key, fig)

    def __delitem__(self, key: str) -> None:
        if key not in self:
            raise KeyError(f"key not found - {key!r}")
        self[key]._setCollection(None)
        super().__delitem__(key)

    def rename(self, src: str, dst: str) -> None:
        if src not in self:
            raise KeyError(f"src not found - {src!r}")
        if src == dst:
            return
        if dst in self:
            raise KeyError(f"dst already exists - {dst!r}")
        fig: Fig = self.pop(src)
        if fig.name != dst:
            fig._setName(dst)
        self.__setitem__(dst, fig)

    def __iter__(self) -> Iterator[Fig]:
        return iter(self.figs)

    def clear(self) -> None:
        for v in self.values():
            v._setCollection(None)
        return super().clear()

    def dump(self, *args, **kwargs) -> str:
        return "\n".join(fig.dump(*args, **kwargs) for fig in self)


class OrderList(list):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__()
        if args == (None,) and not kwargs:
            return
        self.extend(list(*args, **kwargs))

    @property
    def type(self) -> str:
        return self.__class__.__name__

    def __repr__(self) -> str:
        return self.repr()

    def repr(self, prompt: Optional[str] = None) -> str:
        if prompt is None:
            prompt = f"{self.__class__.__name__}"
        return f"{prompt}: {super().__repr__()}"
