"""
This type stub file was generated by pyright.
"""

from .base import PlatformEventLoop
from pyglet.libs.win32.types import *

class Win32EventLoop(PlatformEventLoop):
    def __init__(self) -> None:
        ...
    
    def add_wait_object(self, obj, func): # -> None:
        ...
    
    def remove_wait_object(self, obj): # -> None:
        ...
    
    def start(self): # -> None:
        ...
    
    def step(self, timeout=...): # -> Any:
        ...
    
    def stop(self): # -> None:
        ...
    
    def notify(self): # -> None:
        ...
    
    def set_timer(self, func, interval): # -> None:
        ...
    

