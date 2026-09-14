"""Six-key launcher and request-specific review, shared by every deck size."""

from functools import lru_cache
import math
import threading
import time

from .launch_profiles import HARNESS_NAMES, read_profiles, launch_profile


class Controls:
    def __init__(self, broker, launch=launch_profile, clock=time.monotonic):
        self.broker, self.launch, self.clock = broker, launch, clock
        self.enabled = broker.config.get("controls", {}).get("enabled", False)
        self.lock = threading.RLock()
        self.page = ""
        self.revision = 0
        self.until = 0
        self.offset = 0
        self.profiles = []
        self.profile = None
        self.harness = ""
        self.target = {}
        self.ticket = ""
        self.detail_page = 0
        self.folder_page = 0
        self.message = ""
        self.launching = False
        self.last_launch = -100.0

    @property
    def selected_profile(self):
        if self.profile is None:
            raise ValueError("Choose a repository first")
        return self.profile

    def _page(self, page):
        self.page, self.until = page, self.clock() + self.broker.config.get("controls", {}).get("menu_timeout", 45)
        self.revision += 1

    def _repos(self):
        self.profiles = read_profiles(self.broker.root / "launcher.ini")
        self.offset = 0
        if not self.profiles:
            self.message = "Add repo profiles to launcher.ini"
            self._page("message")
        else:
            self._page("repos")

    def open(self, view):
        with self.lock:
            if not self.enabled or self.launching:
                return
            current = self.broker.registry.view()
            slot = view.get("slot")
            if type(slot) is not int or not 0 <= slot < len(current):
                return
            if any(current[slot].get(k) != view.get(k) for k in ("id", "generation")):
                return
            self.target = dict(view)
            try:
                if view.get("id"):
                    self._page("session")
                else:
                    self._repos()
            except Exception as e:
                self.message = str(e)
                self._page("message")

    def _request(self):
        return next(
            (p for p in self.broker.permissions.pending(self.target.get("id")) if p["ticket"] == self.ticket), None
        )

    def tiles(self):
        with self.lock:
            if not self.page:
                return None
            if self.clock() >= self.until and not self.launching:
                self._page("")
                return None

            def tile(title, subtitle="", action="", value="", tone="blue"):
                return dict(
                    title=title,
                    subtitle=subtitle,
                    _action="controls",
                    command=action,
                    value=value,
                    revision=self.revision,
                    tone=tone,
                )

            back = tile("BACK", "Live sessions", "close")
            blank = tile("")
            if self.page == "requests":
                items = self.broker.permissions.pending(self.target.get("id"))
                result = [
                    tile(p["tool"], p["summary"][:45], "request", p["ticket"], "amber")
                    for p in items[self.offset : self.offset + 4]
                ]
                result += [blank] * (4 - len(result))
                return result + [back, tile("NEXT", f"{len(items)} pending", "next")]
            if self.page in ("repos", "agents"):
                choices = (
                    [(p.name, str(p.directory), "repo", str(i)) for i, p in enumerate(self.profiles)]
                    if self.page == "repos"
                    else [
                        (HARNESS_NAMES[h], self.selected_profile.name, "agent", h)
                        for h in self.selected_profile.harnesses
                    ]
                )
                result = [tile(*v) for v in choices[self.offset : self.offset + 4]]
                result += [blank] * (4 - len(result))
                return result + [back, tile("NEXT", f"{self.offset // 4 + 1}/{(len(choices) + 3) // 4}", "next")]
            if self.page == "session":
                count = len(self.broker.permissions.pending(self.target.get("id")))
                return [
                    tile("SESSION", self.target.get("label", "")),
                    tile("REVIEW", f"{count} request(s)" if count else "Use terminal", "review", tone="amber"),
                    tile("FOCUS", "Open terminal", "focus"),
                    tile("NEW", "Agent + folder", "repos"),
                    blank,
                    back,
                ]
            if self.page == "confirm":
                directory = str(self.selected_profile.directory)
                chunks = [directory[i : i + 45] for i in range(0, len(directory), 45)]
                return [
                    tile("PROJECT", self.selected_profile.name),
                    tile(
                        f"FOLDER {self.folder_page % len(chunks) + 1}/{len(chunks)}",
                        chunks[self.folder_page % len(chunks)],
                        "folder",
                    ),
                    tile("AGENT", HARNESS_NAMES[self.harness]),
                    tile("LAUNCH", "New window", "launch", tone="green"),
                    blank,
                    back,
                ]
            if self.page == "review":
                item = self._request()
                if not item:
                    return [
                        tile("EXPIRED", "Use terminal", tone="amber"),
                        blank,
                        blank,
                        tile("FOCUS", "Open terminal", "focus"),
                        tile("NEXT", "Request", "review"),
                        back,
                    ]
                summary = item["summary"] or "Inspect full request in terminal"
                chunks = [summary[i : i + 45] for i in range(0, len(summary), 45)]
                detail = chunks[self.detail_page % len(chunks)]
                return [
                    tile(item["tool"], item["label"], tone="amber"),
                    tile(f"DETAIL {self.detail_page % len(chunks) + 1}/{len(chunks)}", detail, "detail", tone="amber"),
                    tile("TERMINAL", "Review full input", "terminal"),
                    tile("ACCEPT", "This request only", "allow", tone="green"),
                    tile("REJECT", "This request only", "deny", tone="red"),
                    back,
                ]
            if self.page == "decision":
                state = self.broker.permissions.status(self.ticket)
                message = {
                    "queued": "Waiting for adapter",
                    "delivered": "Adapter received decision",
                    "finished": "Decision sent to harness",
                    "failed": "Not confirmed. Use terminal",
                    "expired": "Not confirmed. Use terminal",
                }.get(state, "Use terminal")
                return [
                    tile("DECISION", message, tone="green" if state == "finished" else "amber"),
                    blank,
                    blank,
                    tile("FOCUS", "Inspect harness", "focus"),
                    tile("REVIEW", "Next request", "review"),
                    back,
                ]
            return [tile("LAUNCHING" if self.launching else "NOTICE", self.message), blank, blank, blank, blank, back]

    def handle(self, view):
        with self.lock:
            if not self.enabled or view.get("revision") != self.revision or not self.page:
                return {"ok": False, "reason": "Stale menu"}
            action = view.get("command")
            if action == "close" and self.launching:
                self._page("")
                return {"ok": True}
            if self.clock() >= self.until or self.launching:
                return {"ok": False, "reason": "Menu expired or launch in progress"}
            try:
                if action == "close":
                    self._page("")
                elif action == "repos":
                    self._repos()
                elif action == "next":
                    count = (
                        len(self.profiles)
                        if self.page == "repos"
                        else len(self.broker.permissions.pending(self.target.get("id")))
                        if self.page == "requests"
                        else len(self.selected_profile.harnesses)
                    )
                    self.offset = (self.offset + 4) if self.offset + 4 < count else 0
                    self._page(self.page)
                elif action == "repo":
                    self.profile = self.profiles[int(view["value"])]
                    self.offset = 0
                    self._page("agents")
                elif action == "agent":
                    self.harness = view["value"]
                    self.folder_page = 0
                    self._page("confirm")
                elif action == "folder":
                    self.folder_page += 1
                    self._page("confirm")
                elif action == "launch":
                    if self.clock() - self.last_launch < 3:
                        raise ValueError("Please wait before launching another session")
                    if all(v["id"] for v in self.broker.registry.view()):
                        raise ValueError("Deck is full. Close a session before launching")
                    self.last_launch = self.clock()
                    self.launching = True
                    self.message = self.selected_profile.name
                    self._page("message")
                    threading.Thread(target=self._launch, args=(self.profile, self.harness), daemon=True).start()
                elif action == "review":
                    items = self.broker.permissions.pending(self.target.get("id"))
                    if items:
                        self.offset = 0
                        self._page("requests")
                    else:
                        self.message = "No live native request. Use Focus to review in your harness."
                        self.broker.handle_press(self.target, synthetic=True)
                        self._page("message")
                elif action == "request":
                    self.ticket = view["value"]
                    self.detail_page = 0
                    self._page("review")
                elif action == "detail":
                    self.detail_page += 1
                    self._page("review")
                elif action in ("allow", "deny", "terminal"):
                    ok = self.broker.permissions.decide(self.ticket, action)
                    self.message = "Decision queued; watch your harness" if ok else "Request expired. Use terminal"
                    if action == "terminal":
                        self.broker.handle_press(self.target, synthetic=True)
                        self.message = "Returned to terminal permission handling"
                    self._page("message" if action == "terminal" else "decision")
                    return {"ok": ok}
                elif action == "focus":
                    outcome = self.broker.handle_press(self.target, synthetic=True)
                    self._page("")
                    return outcome
                return {"ok": True}
            except Exception as e:
                self.message = str(e)
                self._page("message")
                return {"ok": False, "reason": self.message}

    def _launch(self, profile, harness):
        try:
            self.launch(profile, harness)
            message = "Window requested. Waiting for harness registration."
        except Exception as e:
            message = str(e)
        with self.lock:
            self.launching = False
            self.message = message
            if self.page:
                self._page("message")


@lru_cache(maxsize=384)
def control_frame(title, subtitle, tone="blue", phase=0, size=80):
    from PIL import Image, ImageDraw, ImageFont
    from .security import scrub_text

    color = {"blue": (81, 193, 255), "green": (71, 234, 158), "red": (255, 88, 109), "amber": (255, 195, 89)}[tone]
    im = Image.new("RGB", (160, 160), (5, 10, 18))
    draw = ImageDraw.Draw(im)
    gain = 0.65 + 0.12 * math.sin(phase / 24 * 2 * math.pi)
    border = tuple(int(x * gain) for x in color)
    draw.rounded_rectangle((3, 3, 156, 156), radius=19, outline=border, width=3)
    draw.rounded_rectangle((16, 17, 45, 22), radius=2, fill=color)
    if title == "ACCEPT":
        draw.line(((122, 18), (130, 26), (146, 10)), fill=color, width=4)
    elif title == "REJECT":
        draw.line(((126, 10), (143, 27)), fill=color, width=4)
        draw.line(((143, 10), (126, 27)), fill=color, width=4)
    elif title in ("LAUNCH", "NEW"):
        draw.line(((124, 19), (146, 19)), fill=color, width=3)
        draw.line(((135, 8), (135, 30)), fill=color, width=3)
    elif title in ("BACK", "NEXT"):
        direction = -1 if title == "BACK" else 1
        draw.line(((123, 19), (146, 19)), fill=color, width=3)
        tip = 135 + direction * 11
        draw.line(((tip - direction * 7, 12), (tip, 19), (tip - direction * 7, 26)), fill=color, width=3)
    else:
        harness = next((h for h, name in HARNESS_NAMES.items() if name == title), None)
        if harness:
            from .art import harness_logo

            logo = harness_logo(harness, 26)
            if logo:
                im.paste(logo, (122, 8), logo)
    title = scrub_text(title)
    font_size = 21
    while font_size > 12 and draw.textlength(title, font=ImageFont.load_default(size=font_size)) > 140:
        font_size -= 1
    draw.text((14, 39), title[:24], font=ImageFont.load_default(size=font_size), fill=color)
    text = scrub_text(subtitle)
    font = ImageFont.load_default(size=15)
    lines, line = [], ""
    for char in text:
        if draw.textlength(line + char, font=font) > 132:
            lines.append(line)
            line = ""
        line += char
    lines.append(line)
    if len(lines) > 4:
        lines = lines[:4]
        lines[-1] = lines[-1][:-3] + "..."
    for i, line in enumerate(lines):
        draw.text((14, 72 + i * 17), line, font=font, fill=(220, 232, 243))
    return im.resize((size, size), Image.Resampling.LANCZOS)


@lru_cache(maxsize=25)
def hold_frame(progress):
    from PIL import ImageDraw

    image = control_frame("RELEASE" if progress == 24 else "HOLD", "Open controls").copy()
    draw = ImageDraw.Draw(image)
    draw.line((8, 74, 8 + int(64 * progress / 24), 74), fill=(81, 193, 255), width=2)
    return image
