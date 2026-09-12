"""Focus existing Windows top-level windows; never launch from a press."""

import ctypes
from ctypes import wintypes
import os
import time


def activate(record):
    if os.name != "nt":
        return {"ok": False, "reason": "Windows host required"}
    u = ctypes.WinDLL("user32", use_last_error=True)
    u.GetForegroundWindow.restype = wintypes.HWND
    u.IsWindowVisible.argtypes = [wintypes.HWND]
    u.IsIconic.argtypes = [wintypes.HWND]
    u.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    u.SetForegroundWindow.argtypes = [wintypes.HWND]
    u.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    u.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    u.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    u.GetWindowThreadProcessId.restype = wintypes.DWORD
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    u.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]
    # Declare every HWND argument/result explicitly for 64-bit Python.
    for name in ("IsWindow", "IsHungAppWindow"):
        getattr(u, name).argtypes = [wintypes.HWND]
        getattr(u, name).restype = wintypes.BOOL
    u.IsChild.argtypes = [wintypes.HWND, wintypes.HWND]
    u.IsChild.restype = wintypes.BOOL
    u.ShowWindowAsync.argtypes = [wintypes.HWND, ctypes.c_int]
    u.ShowWindowAsync.restype = wintypes.BOOL
    u.GetGUIThreadInfo.argtypes = [wintypes.DWORD, ctypes.POINTER(GUIThreadInfo)]
    u.GetGUIThreadInfo.restype = wintypes.BOOL
    u.PeekMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT, wintypes.UINT]
    u.PeekMessageW.restype = wintypes.BOOL
    u.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.BOOL]
    u.AttachThreadInput.restype = wintypes.BOOL
    u.BringWindowToTop.argtypes = [wintypes.HWND]
    u.BringWindowToTop.restype = wintypes.BOOL
    for name in ("SetFocus", "SetActiveWindow"):
        getattr(u, name).argtypes = [wintypes.HWND]
        getattr(u, name).restype = wintypes.HWND
    token = record.get("windowToken", "")
    candidates = []

    @callback_type
    def collect(hwnd, _):
        if not u.IsWindowVisible(hwnd):
            return True
        text = ctypes.create_unicode_buffer(u.GetWindowTextLengthW(hwnd) + 1)
        u.GetWindowTextW(hwnd, text, len(text))
        pid = wintypes.DWORD()
        u.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if (token and text.value == token) or (not token and pid.value == record["process"]["pid"]):
            candidates.append(hwnd)
        return True

    u.EnumWindows(collect, 0)
    if len(candidates) != 1:
        return {
            "ok": False,
            "reason": "Window mapping ambiguous or absent; use ocdeck launch for a dedicated window",
            "matches": len(candidates),
        }
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentThreadId.restype = wintypes.DWORD
    return focus_window(u, kernel.GetCurrentThreadId(), candidates[0])


class GUIThreadInfo(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("hwndActive", wintypes.HWND),
        ("hwndFocus", wintypes.HWND),
        ("hwndCapture", wintypes.HWND),
        ("hwndMenuOwner", wintypes.HWND),
        ("hwndMoveSize", wintypes.HWND),
        ("hwndCaret", wintypes.HWND),
        ("rcCaret", wintypes.RECT),
    ]


def focus_window(u, current, hwnd, sleep=time.sleep):
    """Activate a resolved window; input attachment is temporary and always undone."""
    target = u.GetWindowThreadProcessId(hwnd, None)
    if not target or not u.IsWindow(hwnd):
        return {"ok": False, "reason": "Target window closed", "hwnd": int(hwnd)}
    if u.IsHungAppWindow(hwnd):
        return {"ok": False, "reason": "Target window is not responding", "hwnd": int(hwnd)}

    def focused_child():
        info = GUIThreadInfo()
        info.cbSize = ctypes.sizeof(info)
        if u.GetGUIThreadInfo(target, ctypes.byref(info)):
            child = info.hwndFocus
            if child and (child == hwnd or u.IsChild(hwnd, child)):
                return child
        return None

    def confirmed():
        return u.GetForegroundWindow() == hwnd and not u.IsIconic(hwnd) and bool(focused_child())

    # Remember the editor/terminal input child before activation, rather than
    # unconditionally moving keyboard focus to its top-level frame.
    child = focused_child()
    if u.IsIconic(hwnd):
        u.ShowWindowAsync(hwnd, 9)  # SW_RESTORE
    accepted = bool(u.SetForegroundWindow(hwnd))
    for _ in range(5):
        if confirmed():
            return {"ok": True, "hwnd": int(hwnd), "method": "SetForegroundWindow", "keyboardFocus": True}
        sleep(0.04)

    # A broker worker is not a GUI thread. Explicitly create its message queue
    # before attaching, and attach BOTH the foreground and destination threads.
    message = wintypes.MSG()
    u.PeekMessageW(ctypes.byref(message), None, 0, 0, 0)  # PM_NOREMOVE
    foreground = u.GetForegroundWindow()
    other = u.GetWindowThreadProcessId(foreground, None) if foreground else 0
    attached, failed = [], []
    try:
        for thread in dict.fromkeys((other, target)):
            if not thread or thread == current:
                continue
            if u.AttachThreadInput(current, thread, True):
                attached.append(thread)
            else:
                failed.append(thread)
        if u.IsWindow(hwnd):
            u.BringWindowToTop(hwnd)
            u.SetForegroundWindow(hwnd)
            if target == current or target in attached:
                u.SetActiveWindow(hwnd)
                # Prefer the application's current focus after activation, then
                # its previously focused child if it still belongs to this frame.
                focus = focused_child()
                if not focus and child and u.IsWindow(child) and u.IsChild(hwnd, child):
                    focus = child
                u.SetFocus(focus or hwnd)
    finally:
        for thread in reversed(attached):
            u.AttachThreadInput(current, thread, False)
    for _ in range(5):
        if confirmed():
            return {"ok": True, "hwnd": int(hwnd), "method": "AttachThreadInput", "keyboardFocus": True}
        sleep(0.04)
    return {
        "ok": False,
        "reason": "Windows denied foreground or keyboard focus",
        "hwnd": int(hwnd),
        "apiAccepted": accepted,
        "foreground": int(u.GetForegroundWindow() or 0),
        "keyboardFocus": bool(focused_child()),
        "attachmentFailures": failed,
    }
