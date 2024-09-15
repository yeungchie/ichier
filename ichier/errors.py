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
