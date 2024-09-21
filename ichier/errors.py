__all__ = [
    "ICHierError",
    "InstanceError",
    "ModuleError",
    "NetError",
    "ParameterError",
    "TerminalError",
]


class ICHierError(Exception):
    pass


class InstanceError(ICHierError):
    pass


class ModuleError(ICHierError):
    pass


class NetError(ICHierError):
    pass


class ParameterError(ICHierError):
    pass


class TerminalError(ICHierError):
    pass
