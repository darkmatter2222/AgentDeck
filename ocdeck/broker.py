import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
from .observability import configure, tail, correlation
from .alerts import Alerts
from .security import scrub
import uuid
import os
from pathlib import Path
import queue
import secrets
import threading
import time
import urllib.parse

from .common import alive, atomic_json, home, identity, read_json, load_config
from .device import DeviceLoop
from .focus import activate
from .model import Registry
from .errors import message
from .settings import validate_config
from .direct_hooks import DirectHooks

LOG = logging.getLogger(__name__)


class InstanceLock:
    def __init__(self, root):
        self.path = root / "broker.lock"

    def __enter__(self):
        self.f = open(self.path, "a+b")
        try:
            self.f.seek(0)
            if os.name == "nt":
                import msvcrt

                if not self.f.read(1):
                    self.f.write(b"0")
                    self.f.flush()
                self.f.seek(0)
                msvcrt.locking(self.f.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(self.f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except Exception:
            self.f.close()
            raise
        return self

    def __exit__(self, *args):
        self.f.close()


class Broker:
    def __init__(self, root=None, mock=False, probe=alive, focus=activate):
        self.root = Path(root or home())
        self.root.mkdir(parents=True, exist_ok=True)
        saved = load_config(self.root)
        from .world_settings import read_ini

        saved["world"] = {**saved.get("world", {}), **read_ini(self.root)}
        validate_config(saved)
        self.config = {
            "fps": 24,
            "brightness": 45,
            "animations": True,
            "ready": True,
            "check_updates": not mock,
            "auto_restart_on_upgrade": not mock,
            **saved,
        }
        if not (self.root / "token").exists():
            fd = os.open(self.root / "token", os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(fd, "w", encoding="ascii") as f:
                f.write(secrets.token_hex(32))
        self.token = (self.root / "token").read_text(encoding="ascii").strip()
        self.registry = Registry(probe, slots=self.config.get("slots", 6), secrets=(self.token,))
        self.direct_hooks = DirectHooks(self.registry)
        self.alerts = Alerts(self.config)
        self.update = None
        self.stop = threading.Event()
        self.presses = queue.Queue(maxsize=64)
        self.device = DeviceLoop(self.registry, self.presses, self.stop, self.config, mock, root=self.root)
        self.focus = focus
        self.last_focus = None
        self.last_press = {}
        self.server = None
        from .permissions import Permissions
        from .controls import Controls

        self.permissions = Permissions(
            self.registry,
            self.config.get("controls", {}).get("enabled", False)
            and self.config.get("controls", {}).get("permissions", False),
            timeout=self.config.get("controls", {}).get("request_timeout", 110),
        )
        self.controls = Controls(self)
        self.device.controls = self.controls

    def dispatch(self, method, path, body):
        if method == "GET" and path == "/v1/control-capabilities":
            return {"permissions": self.permissions.enabled, "launcher": self.controls.enabled}
        if method == "POST" and path in ("/v1/permissions/offer", "/v1/permissions/poll", "/v1/permissions/finish"):
            return getattr(self.permissions, path.rsplit("/", 1)[1])(body)
        if method == "GET" and path == "/v1/status":
            with self.registry.lock:
                overflow = sum(r["slot"] is None for r in self.registry.records.values())
            return {
                "epoch": self.registry.epoch,
                "device": dict(self.device.status),
                "slots": self.registry.view(),
                "overflow": overflow,
                "lastFocus": scrub(self.last_focus, (self.token,)),
                "brokerPid": os.getpid(),
                "recentErrors": tail(self.root, 10, errors_only=True),
                "update": self.update,
            }
        if method == "POST" and path == "/v1/register":
            record = self.registry.upsert(body)
            return {"epoch": self.registry.epoch, "slot": record["slot"]}
        if method == "POST" and path == "/v1/hook":
            return self.direct_hooks.event(body)
        if path.startswith("/v1/instances/"):
            key = urllib.parse.unquote(path[len("/v1/instances/") :])
            if method == "PUT":
                with self.registry.lock:
                    accepted = self.registry.snapshot(key, body)
                    if accepted:
                        self.alerts.observe(self.registry.view())
                return {"accepted": accepted, "epoch": self.registry.epoch}
            if method == "DELETE":
                self.registry.remove(key)
                return {"ok": True}
        if method == "POST" and path == "/v1/focus":
            return self.handle_press(body, synthetic=True)
        if method == "POST" and path == "/v1/stop":
            self.stop.set()
            return {"ok": True}
        raise KeyError("Unknown route")

    def handle_press(self, view, synthetic=False):
        if not synthetic and view.get("_action") == "controls":
            return self.controls.handle(view)
        if not synthetic and view.get("_action") == "open_controls":
            self.controls.open(view)
            return {"ok": True}
        if not synthetic and view.get("_action") == "open_world_help":
            import webbrowser
            from .world import HELP_URL

            try:
                return {"ok": bool(webbrowser.open(HELP_URL, new=2))}
            except Exception:
                return {"ok": False}
        # Only the physical/render queues can request these local actions.
        if not synthetic and view.get("_action") == "open_coffee":
            import webbrowser
            from .coffee import SUPPORT_URL

            try:
                opened = bool(webbrowser.open(SUPPORT_URL, new=2))
                self.device.status["coffee_browser"] = {"ok": opened}
                LOG.info("Coffee browser opened=%s", opened)
                return {"ok": opened}
            except Exception:
                LOG.exception("Could not open coffee page")
                return {"ok": False}
        if not synthetic and view.get("_action") == "update" and not view.get("id"):
            slot = view.get("slot")
            current = self.registry.view()
            if (
                type(slot) is int
                and 0 <= slot < len(current)
                and not current[slot].get("id")
                and current[slot].get("generation") == view.get("generation")
            ):
                return {"ok": getattr(self.device, "_start_jelly_update")()}
            return {"ok": False, "reason": "Empty or stale slot"}
        r = self.registry.resolve(view.get("slot"), view.get("generation"), view.get("id"))
        if not r:
            return {"ok": False, "reason": "Empty or stale slot"}
        now = time.monotonic()
        if now - self.last_press.get(r["id"], -100) < 0.2:
            return {"ok": False, "reason": "Debounced"}
        self.last_press[r["id"]] = now
        outcome = self.focus(r)
        if not outcome.get("ok"):
            outcome = {**outcome, "fix": message("AD006")}
        self.last_focus = {**outcome, "id": r["id"], "synthetic": synthetic, "time": time.time()}
        if outcome.get("ok"):
            self.device.notify_jelly("focus", r["slot"])
        LOG.info("Focus %s", self.last_focus)
        return self.last_focus

    def check_update(self):
        from .updates import check

        self.update = check(self.root, self.config)

    def serve(self):
        broker = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.0"

            def setup(self):
                super().setup()
                self.connection.settimeout(3)

            def log_message(self, *args):
                pass

            def handle_request(self):
                context = correlation.set(uuid.uuid4().hex)
                try:
                    if self.headers.get("Origin"):
                        self.send_json(403, {"error": message("AD007", "Browser origins are not accepted")})
                        return
                    expected = "Bearer " + broker.token
                    if not hmac.compare_digest(self.headers.get("Authorization", ""), expected):
                        self.send_json(401, {"error": message("AD007")})
                        return
                    size = int(self.headers.get("Content-Length", "0"))
                    if not 0 <= size <= 65536:
                        self.send_json(413, {"error": message("AD004", "Body too large")})
                        return
                    raw = self.rfile.read(size)
                    if len(raw) != size:
                        raise ValueError("Incomplete body")
                    data = json.loads(raw) if raw else {}
                    if not isinstance(data, dict):
                        raise ValueError("Expected object")
                    result = broker.dispatch(self.command, urllib.parse.urlsplit(self.path).path, data)
                    self.send_json(200, result)
                except KeyError:
                    self.send_json(404, {"error": message("AD005")})
                except (ValueError, TypeError) as e:
                    self.send_json(400, {"error": message("AD004", str(e))})
                except Exception:
                    LOG.exception(message("AD500"))
                    self.send_json(500, {"error": message("AD500")})
                finally:
                    correlation.reset(context)

            def send_json(self, code, value):
                data = json.dumps(scrub(value, (broker.token,))).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                try:
                    self.wfile.write(data)
                except OSError:
                    pass

            do_GET = do_POST = do_PUT = do_DELETE = handle_request

        class Server(ThreadingHTTPServer):
            daemon_threads = True

            def __init__(self, *args):
                self.limit = threading.BoundedSemaphore(16)
                super().__init__(*args)

            def process_request(self, sock, address):
                if not self.limit.acquire(blocking=False):
                    sock.close()
                    return
                try:
                    super().process_request(sock, address)
                except Exception:
                    self.limit.release()
                    raise

            def process_request_thread(self, *args):
                try:
                    super().process_request_thread(*args)
                finally:
                    self.limit.release()

        self.server = Server(("127.0.0.1", 0), Handler)
        atomic_json(
            self.root / "discovery.json",
            {"port": self.server.server_address[1], "epoch": self.registry.epoch, "process": identity()},
        )
        threads = [
            threading.Thread(target=self.server.serve_forever, daemon=True),
            threading.Thread(target=self.device.run, daemon=True),
            threading.Thread(target=self.alerts.run, args=(self.stop,), daemon=True),
            threading.Thread(target=self.check_update, daemon=True),
        ]
        if self.config.get("auto_restart_on_upgrade", True):
            from .upgrade_watch import watch

            threads.append(threading.Thread(target=watch, args=(self,), daemon=True))
        for thread in threads:
            thread.start()
        LOG.info("Broker ready on OS-assigned port %s", self.server.server_address[1])
        try:
            next_sweep = 0
            while not self.stop.is_set():
                if time.monotonic() >= next_sweep:
                    self.registry.sweep()
                    next_sweep = time.monotonic() + 0.5
                try:
                    self.handle_press(self.presses.get(timeout=0.1))
                except queue.Empty:
                    pass
                except Exception:
                    LOG.exception(message("AD006"))
        finally:
            self.stop.set()
            self.server.shutdown()
            self.server.server_close()
            for thread in threads:
                thread.join(timeout=3)
            discovery = read_json(self.root / "discovery.json", {})
            if discovery.get("epoch") == self.registry.epoch:
                (self.root / "discovery.json").unlink(missing_ok=True)


def run(root=None, mock=False):
    root = Path(root or home())
    root.mkdir(parents=True, exist_ok=True)
    try:
        with InstanceLock(root):
            broker = Broker(root, mock=mock)
            configure(root)
            import signal

            for sig in (signal.SIGINT, signal.SIGTERM):
                signal.signal(sig, lambda *_: broker.stop.set())
            broker.serve()
    except (BlockingIOError, PermissionError):
        LOG.info(message("AD008"))
