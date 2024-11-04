from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, Optional, Literal, Union
from uuid import uuid4

import ichier.obj as icobj
from .fig import Fig, FigCollection

__all__ = [
    "Design",
    "DesignCollection",
]


class Design(Fig):
    def __init__(
        self,
        name: Optional[str] = None,
        modules: Iterable[icobj.Module] = (),
        parameters: dict = {},
    ) -> None:
        if name is None:
            name = str(uuid4())[:8]
        self.name = name
        self.__modules = icobj.ModuleCollection(self, modules)
        self.__parameters = icobj.ParameterCollection(parameters)
        self.__includes = DesignCollection(self)
        self.__path = None

    @property
    def modules(self) -> icobj.ModuleCollection:
        return self.__modules

    @property
    def parameters(self) -> icobj.ParameterCollection:
        return self.__parameters

    @property
    def includes(self) -> "DesignCollection":
        return self.__includes

    @property
    def path(self) -> Optional[Path]:
        return self.__path

    @path.setter
    def path(self, value: Optional[Union[str, Path]]) -> None:
        self.__path = None if value is None else Path(value)

    def summary(
        self,
        info_type: Literal["compact", "detail"] = "compact",
    ) -> Dict[str, Any]:
        if info_type == "compact":
            return {
                "name": self.name,
                "modules": len(self.modules),
            }
        elif info_type == "detail":
            return {
                "name": self.name,
                "parameters": self.parameters.summary(),
                "modules": self.modules.summary(info_type=info_type),
            }
        else:
            raise ValueError("Invalid type")


class DesignCollection(FigCollection):
    def _valueChecker(self, value: Design) -> None:
        if not isinstance(value, Design):
            raise TypeError("value must be a Design")

    def __iter__(self) -> Iterator[Design]:
        return iter(self.figs)

    def __getitem__(self, key: Union[int, str]) -> Design:
        return super().__getitem__(key)

    def get(self, *args: Any, **kwargs: Any) -> Optional[Design]:
        return super().get(*args, **kwargs)
