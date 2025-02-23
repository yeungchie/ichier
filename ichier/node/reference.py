from typing import Optional
from . import obj

__all__ = [
    "Reference",
    "DesignateReference",
    "Unknown",
]


class Reference(str):
    def __new__(cls, name: str, instance: Optional[obj.Instance] = None):
        return super().__new__(cls, name)

    def __init__(self, name: str, instance: Optional[obj.Instance] = None) -> None:
        if instance is not None and not isinstance(instance, obj.Instance):
            raise TypeError("instance must be an Instance")
        self.__name = str(self)
        self.__instance = instance

    def __repr__(self) -> str:
        return f"{self.type}({super().__repr__()})"

    def __str__(self) -> str:
        return super().__str__()

    @property
    def type(self) -> str:
        return self.__class__.__name__

    @property
    def name(self) -> str:
        return self.__name

    @property
    def instance(self) -> Optional[obj.Instance]:
        return self.__instance

    def getMaster(self) -> Optional[obj.Module]:
        if self.instance is None:
            return
        design = self.instance.getDesign()
        if design is None:
            return
        return design.modules.get(self.name)


class DesignateReference(Reference):
    def getMaster(self) -> None:
        pass


class Unknown:
    def __init__(self, instance: Optional[obj.Instance] = None) -> None:
        if instance is not None and not isinstance(instance, obj.Instance):
            raise TypeError("instance must be an Instance")
        self.__instance = instance

    def __repr__(self) -> str:
        return self.name

    @property
    def type(self) -> str:
        return self.__class__.__name__

    @property
    def name(self) -> str:
        return self.type

    @property
    def instance(self) -> Optional[obj.Instance]:
        return self.__instance

    def getMaster(self) -> None:
        pass
