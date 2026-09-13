__version__ = "3.0.5"

from . import jelly_art as _jelly_art
from .jelly_cute import install as _install_jelly_cute

_install_jelly_cute(_jelly_art)

from . import device as _device
from .jelly_update import install_device_patch as _install_jelly_update

_install_jelly_update(_device.DeviceLoop)

from . import broker as _broker
from .jelly_update import install_broker_patch as _install_broker_update

_install_broker_update(_broker.Broker)

del _broker, _device, _install_broker_update, _install_jelly_cute, _install_jelly_update, _jelly_art
