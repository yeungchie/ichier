from typing import Any, Iterable, Optional, Union
from typing_extensions import Self

import ichier

__all__ = [
    "Fig",
    "Collection",
    "FigCollection",
]


class Fig:
    __name: str = ""
    __collection: Optional["FigCollection"] = None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={repr(self.name)})"

    def __str__(self) -> str:
        return self.name

    @property
    def name(self) -> str:
        return self.__name

    @name.setter
    def name(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("name must be a string")
        if value == self.name:
            return
        old = self.name
        self.__name = value
        if self.collection is not None:
            self.collection.rename(old, value)

    @property
    def collection(self) -> Optional["FigCollection"]:
        return self.__collection

    def _setCollection(self, value: Optional["FigCollection"]) -> None:
        if value is not None and not isinstance(value, FigCollection):
            raise TypeError("value must be a FigCollection or None")
        self.__collection = value


class Collection(dict):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__()
        self.update(*args, **kwargs)

    def _keyChecker(self, key: str) -> None:
        if not isinstance(key, str):
            raise KeyError(f"key must be a string - {repr(key)}")

    def _valueChecker(self, value: Any) -> None:
        pass

    def _dict__setitem__(self, key: str, value) -> None:
        super().__setitem__(key, value)

    def __setitem__(self, key: str, value: Any) -> None:
        self._keyChecker(key)
        self._valueChecker(value)
        self._dict__setitem__(key, value)

    def __getitem__(self, key: Union[int, str]) -> Fig:
        if isinstance(key, int):
            key = tuple(self.keys())[key]
        elif isinstance(key, str):
            pass
        else:
            raise KeyError("key must be an integer or a string")
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
            raise KeyError(f"{key} not found")
        self.__delitem__(key)

    def setdefault(self, *args, **kwargs) -> None:
        raise NotImplementedError("setdefault() is disabled")

    def __or__(self, other: "Collection") -> "Collection":
        if not isinstance(other, Collection):
            raise TypeError("other must be a Collection")
        result = Collection()
        result.update(self)
        result.update(other)
        return result

    def __ror__(self, other: "Collection") -> "Collection":
        if not isinstance(other, Collection):
            raise TypeError("other must be a Collection")
        result = Collection()
        result.update(other)
        result.update(self)
        return result

    def __ior__(self, other: dict) -> Self:
        self.update(other)
        return self


class FigCollection(Collection):
    def __init__(
        self,
        parent: Union["ichier.Module", "ichier.Design"],
        figs: Iterable[Fig] = (),
    ) -> None:
        super().__init__()
        self.__parent = parent
        self.extend(figs)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: {len(self)} figs"

    @property
    def parent(self) -> Union["ichier.Module", "ichier.Design"]:
        return self.__parent

    @property
    def order(self) -> tuple:
        return tuple(self.keys())

    @property
    def figs(self) -> tuple:
        return tuple(self.values())

    def _valueChecker(self, value: Fig) -> None:
        if not isinstance(value, Fig):
            raise TypeError("value must be a Fig")

    def __setitem__(self, key: str, fig: Fig) -> None:
        self._keyChecker(key)
        self._valueChecker(fig)
        if key in self:
            del self[key]
        fig._setCollection(self)
        super()._dict__setitem__(key, fig)

    def __delitem__(self, key: str) -> None:
        if key not in self:
            raise KeyError(f"{key} not found")
        self[key]._setCollection(None)
        super().__delitem__(key)

    def rename(self, src: str, dst: str) -> None:
        if src not in self:
            raise KeyError(f"{src} not found")
        if src == dst:
            return
        if dst in self:
            raise KeyError(f"{dst} already exists")
        fig: Fig = self.pop(src)
        if fig.name != dst:
            fig.name = dst
        self.__setitem__(dst, fig)
