"""Device control module"""

from .device_controller import DeviceController
from .android_device import AndroidDevice

try:
    from .ios_device import IOSDevice
except ImportError:
    IOSDevice = None

__all__ = ['DeviceController', 'AndroidDevice', 'IOSDevice']