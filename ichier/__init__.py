from .parameter import ParameterCollection
from .instance import Instance, InstanceCollection
from .module import Module, ModuleCollection
from .net import Net, NetCollection
from .terminal import Terminal, TerminalCollection
from .design import Design, DesignCollection

from . import release

__author__ = release.author
__email__ = release.email
__license__ = release.license
__version__ = release.version
__url__ = release.url
__copyright__ = release.copyright

__all__ = [
    "Design",
    "DesignCollection",
    "Module",
    "ModuleCollection",
    "Instance",
    "InstanceCollection",
    "Net",
    "NetCollection",
    "Terminal",
    "TerminalCollection",
    "ParameterCollection",
]
