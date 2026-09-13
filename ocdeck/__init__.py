__version__ = "3.0.0"

from . import jelly_art as _jelly_art
from .jelly_cute import install as _install_jelly_cute

_install_jelly_cute(_jelly_art)

del _install_jelly_cute, _jelly_art
