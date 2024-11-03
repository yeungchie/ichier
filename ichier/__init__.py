from . import release

__author__ = release.author
__email__ = release.email
__license__ = release.license
__version__ = release.version
__url__ = release.url
__copyright__ = release.copyright

from .obj import Design, Module, Instance, Net, Terminal

__all__ = [
    "Design",
    "Module",
    "Instance",
    "Net",
    "Terminal",
]
