from typing import Any, Dict, Iterable, Optional
from typing_extensions import Literal
from uuid import uuid4

import ichier
from .fig import Fig


class Design(Fig):
    def __init__(
        self,
        name: Optional[str] = None,
        modules: Iterable[ichier.Module] = (),
        parameters: dict = {},
    ) -> None:
        if name is None:
            name = str(uuid4())[:8]
        self.name = name
        self.__modules = ichier.ModuleCollection(self, modules)
        self.__parameters = ichier.ParameterCollection(parameters)

    @property
    def modules(self) -> ichier.ModuleCollection:
        return self.__modules

    @property
    def parameters(self) -> ichier.ParameterCollection:
        return self.__parameters

    def summary(
        self,
        info_type: Literal["compact", "detail"] = "compact",
    ) -> Dict[str, Any]:
        if info_type == "compact":
            return {
                "name": self.name,
                "parameters": len(self.parameters),
                "modules": self.modules.summary(info_type=info_type),
            }
        elif info_type == "detail":
            return {
                "name": self.name,
                "parameters": self.parameters.summary(),
                "modules": self.modules.summary(info_type=info_type),
            }
        else:
            raise ValueError("Invalid type")
