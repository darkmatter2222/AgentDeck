"""Focus an existing Windows window associated with a registered harness process."""

import ctypes
from ctypes import wintypes
import os
import time


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


def _windll(name):
    """Resolve the Windows-only ctypes loader without exposing it to non-Windows type stubs."""
    return getattr(ctypes, "WinDLL")(name, use_last_error=True)


def _api():
    u = _windll("user32")
    u.GetForegroundWindow.restype = wintypes.HWND
    u.IsWindowVisible.argtypes = [wintypes.HWND]
    u.IsIconic.argtypes = [wintypes.HWND]
    u.SetForegroundWindow.argtypes = [wintypes.HWND]
    u.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    u.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    u.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    u.GetWindowThreadProcessId.restype = wintypes.DWORD
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
    for name in ("IsWindow", "IsHungAppWindow"):
        getattr(u, name).argtypes = [wintypes.HWND]
        getattr(u, name).restype = wintypes.BOOL
    for name in ("SetFocus", "SetActiveWindow"):
        getattr(u, name).argtypes = [wintypes.HWND]
        getattr(u, name).restype = wintypes.HWND
    return u


def _pid_chain(pid):
    try:
        import psutil

        process = psutil.Process(int(pid))
        result = [process.pid]
        for parent in process.parents()[:12]:
            result.append(parent.pid)
        return result
    except Exception:
        return [int(pid)] if str(pid).isdigit() else []


def _owner_pid(u, hwnd):
    pid = wintypes.DWORD()
    u.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return int(pid.value)


def capture_window(pid):
    """Capture the visible ancestor window for a native hook's harness process."""
    if os.name != "nt":
        return {}
    u = _api()
    chain = _pid_chain(pid)
    if not chain:
        return {}
    distance = {value: index for index, value in enumerate(chain)}
    foreground = u.GetForegroundWindow()
    if foreground and u.IsWindowVisible(foreground):
        owner = _owner_pid(u, foreground)
        if owner in distance:
            return {"windowHwnd": int(foreground), "windowPid": owner}
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    candidates = []

    @callback_type
    def collect(hwnd, _):
        if u.IsWindowVisible(hwnd):
            owner = _owner_pid(u, hwnd)
            if owner in distance:
                candidates.append((distance[owner], int(hwnd), owner))
        return True

    u.EnumWindows(collect, 0)
    if not candidates:
        return {}
    best = min(item[0] for item in candidates)
    nearest = [item for item in candidates if item[0] == best]
    if len(nearest) != 1:
        return {}
    _, hwnd, owner = nearest[0]
    return {"windowHwnd": hwnd, "windowPid": owner}


def activate(record):
    if os.name != "nt":
        return {"ok": False, "reason": "Windows host required"}
    u = _api()
    stored = int(record.get("windowHwnd", 0) or 0)
    if stored and u.IsWindow(stored) and u.IsWindowVisible(stored):
        candidates = [stored]
    else:
        token = record.get("windowToken", "")
        chain = _pid_chain(record.get("process", {}).get("pid", 0))
        if record.get("windowPid") and int(record["windowPid"]) not in chain:
            chain.insert(0, int(record["windowPid"]))
        distance = {value: index for index, value in enumerate(chain)}
        token_candidates = []
        process_candidates = []
        callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        @callback_type
        def collect(hwnd, _):
            if not u.IsWindowVisible(hwnd):
                return True
            length = u.GetWindowTextLengthW(hwnd)
            title = ctypes.create_unicode_buffer(length + 1)
            u.GetWindowTextW(hwnd, title, len(title))
            owner = _owner_pid(u, hwnd)
            if token and title.value == token:
                token_candidates.append(int(hwnd))
            elif not token and owner in distance:
                process_candidates.append((distance[owner], int(hwnd)))
            return True

        u.EnumWindows(collect, 0)
        if token:
            candidates = token_candidates
        elif process_candidates:
            best = min(item[0] for item in process_candidates)
            candidates = [hwnd for dist, hwnd in process_candidates if dist == best]
        else:
            candidates = []
    if len(candidates) != 1:
        return {
            "ok": False,
            "reason": "Window mapping ambiguous or absent; keep one harness per OS window for one-touch focus",
            "matches": len(candidates),
        }
    kernel = _windll("kernel32")
    kernel.GetCurrentThreadId.restype = wintypes.DWORD
    return focus_window(u, kernel.GetCurrentThreadId(), candidates[0])


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

    child = focused_child()
    if u.IsIconic(hwnd):
        u.ShowWindowAsync(hwnd, 9)
    accepted = bool(u.SetForegroundWindow(hwnd))
    for _ in range(5):
        if confirmed():
            return {"ok": True, "hwnd": int(hwnd), "method": "SetForegroundWindow", "keyboardFocus": True}
        sleep(0.04)

    message = wintypes.MSG()
    u.PeekMessageW(ctypes.byref(message), None, 0, 0, 0)
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
