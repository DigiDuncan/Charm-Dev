from collections.abc import Callable
from typing import Any, Literal
__all__ = ('copy', 'paste', 'waitForPaste', 'waitForNewPaste', 'set_clipboard', 'determine_clipboard')

__version__ = ...
HAS_DISPLAY = ...
EXCEPT_MSG = ...
PY2 = ...
STR_OR_UNICODE = ...
ENCODING = ...
class PyperclipException(RuntimeError): ...
class PyperclipWindowsException(PyperclipException):
    def __init__(self, message: str) -> None: ...
class PyperclipTimeoutException(PyperclipException): ...
def init_osx_pbcopy_clipboard() -> tuple[Callable[..., None], Callable[[], str]]: ...
def init_osx_pyobjc_clipboard() -> tuple[Callable[..., None], Callable[[], Any]]: ...
def init_gtk_clipboard() -> tuple[Callable[..., None], Callable[[], Any | Literal['']]]: ...
def init_qt_clipboard() -> tuple[Callable[..., None], Callable[[], str | Any]]: ...
def init_xclip_clipboard() -> tuple[Callable[..., None], Callable[..., str]]: ...
def init_xsel_clipboard() -> tuple[Callable[..., None], Callable[..., str]]: ...
def init_wl_clipboard() -> tuple[Callable[..., None], Callable[..., str]]: ...
def init_klipper_clipboard() -> tuple[Callable[..., None], Callable[[], str]]: ...
def init_dev_clipboard_clipboard() -> tuple[Callable[..., None], Callable[[], str]]: ...
def init_no_clipboard() -> tuple[ClipboardUnavailable, ClipboardUnavailable]: ...
class ClipboardUnavailable: ...
class CheckedCall:
    def __init__(self, f) -> None: ...
    def __call__(self, *args): ...
    def __setattr__(self, key, value) -> None: ...
def init_windows_clipboard() -> tuple[Callable[..., None], Callable[[], str | None]]: ...
def init_wsl_clipboard() -> tuple[Callable[..., None], Callable[[], str]]: ...
def determine_clipboard() -> tuple[Callable[..., None], Callable[[], str]] | tuple[Callable[..., None], Callable[..., str]] | tuple[ClipboardUnavailable, ClipboardUnavailable]: ...
def set_clipboard(clipboard) -> None: ...
def lazy_load_stub_copy(text) -> None: ...
def lazy_load_stub_paste() -> str: ...
def is_available() -> bool: ...
def waitForPaste(timeout=...) -> str | None: ...
def waitForNewPaste(timeout=...) -> str | None: ...
def copy(text: str) -> None: ...
def paste() -> str: ...
