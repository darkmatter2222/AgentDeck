"""Original procedural artwork. No downloaded assets or image-generation dependency."""
import math
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from .appearance import Appearance, THEMES, HARNESS_NAMES

PALETTE = {"running": (32, 235, 117), "idle": (255, 179, 46),
           "input": (255, 55, 75), "ready": (50, 204, 255), "unknown": (255, 179, 46)}
LABELS = {"running": "RUNNING", "idle": "IDLE", "input": "INPUT", "ready": "READY", "unknown": "LINK ?"}


@lru_cache(maxsize=1024)
def frame(state, label, slot, phase, size=80, style=Appearance(), harness="opencode", detail=""):
    image = Image.new("RGB", (size, size), "black")
    if state == "off":
        return image
    # Draw at 2x for smooth curves, then downsample. Discrete phases bound cache size; one cycle has 96 phases.
    im = Image.new("RGB", (160, 160), (3, 6, 10))
    d = ImageDraw.Draw(im)
    color = tuple(bytes.fromhex(THEMES[style.theme][list(PALETTE).index(state)]))
    t = phase / 96 * 2 * math.pi
    pulse = (1 + math.sin(t)) / 2
    power = 0.45 + 0.55 * pulse if state == "input" else 0.55 + 0.25 * pulse
    power = 1 - style.intensity * (1 - power)
    c = tuple(int(x * power) for x in color)
    d.rounded_rectangle((3, 3, 156, 156), radius=22, fill=tuple(int(x * .08) for x in c), outline=c, width=3)
    if style.layout == "harness" and state != "ready":
        draw_harness(d, harness, color)
        d.ellipse((128, 13, 147, 32), fill=c, outline="white", width=2)
    elif style.layout == "minimal" and state != "ready":
        d.ellipse((61, 34, 99, 72), fill=c)
        d.text((80, 53), {"running":">", "idle":"II", "input":"!", "unknown":"?"}.get(state,"+"),
               font=ImageFont.load_default(size=24), fill="black", anchor="mm")
    elif state == "running":
        d.ellipse((48, 23, 112, 87), outline=tuple(int(x * .2) for x in color), width=5)
        d.arc((48, 23, 112, 87), phase * 3.75, phase * 3.75 + 110, fill=color, width=6)
        d.polygon([(74, 42), (74, 69), (94, 55)], fill=color)
    elif state == "input":
        radius = 22 + int(pulse * 8)
        d.ellipse((80-radius, 54-radius, 80+radius, 54+radius), fill=c)
        d.rounded_rectangle((77, 35, 83, 57), radius=2, fill=(15, 2, 3))
        d.ellipse((77, 63, 83, 69), fill=(15, 2, 3))
    elif state == "ready":
        d.arc((47, 21, 113, 87), phase*3.75, phase*3.75+270, fill=c, width=3)
        d.line([(64, 53), (76, 65), (98, 41)], fill=color, width=6)
    elif state == "idle":
        d.rounded_rectangle((62, 36, 71, 73), radius=3, fill=c)
        d.rounded_rectangle((89, 36, 98, 73), radius=3, fill=c)
    else:
        d.line([(64, 36), (96, 68)], fill=color, width=5)
        d.line([(96, 36), (64, 68)], fill=color, width=5)
    project = label.split(':', 1)[1] if label.split(':', 1)[0] in HARNESS_NAMES and ':' in label else label
    values = {'status': LABELS[state], 'project': 'DEVICE ONLINE' if state == 'ready' else project,
              'harness': HARNESS_NAMES.get(harness, harness), 'detail': detail,
              'custom': style.custom_text, 'none': ''}
    for field, y, height, fill in [(style.primary, 101, 17, color), (style.secondary, 130, 13, (210,219,228))]:
        text = values[field]
        if style.show_slot and field == 'project' and state != 'ready': text = f'{slot+1}  {text}'
        fit_text(d, text, y, height, fill)
    im = im.resize((size, size), Image.Resampling.LANCZOS)
    gain = style.brightness * (1 - style.intensity * .22 * (1 - pulse) if style.effect == 'glow' else 1)
    return ImageEnhance.Brightness(im).enhance(gain) if gain != 1 else im


def fit_text(draw, text, y, height, fill):
    text = text.encode('ascii', 'replace').decode()
    font = ImageFont.load_default(size=height)
    if draw.textlength(text, font=font) > 140:
        lo, hi = 0, len(text)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if draw.textlength(text[:mid] + '...', font=font) <= 140: lo = mid
            else: hi = mid - 1
        text = text[:lo] + '...'
    draw.text((80,y), text, fill=fill, font=font, anchor='mm')


def draw_harness(d, harness, color):
    """Original small-screen brand-inspired glyphs, not official logo assets."""
    if harness == 'claude':
        for n in range(12):
            t = n * math.pi / 6
            d.line((80+12*math.cos(t),54+12*math.sin(t),80+30*math.cos(t+.08),54+30*math.sin(t+.08)),fill=color,width=5)
    elif harness == 'gemini':
        d.polygon([(80,22),(90,44),(112,54),(90,64),(80,86),(70,64),(48,54),(70,44)], fill=color)
    elif harness.startswith('copilot'):
        d.rounded_rectangle((47,32,113,76),radius=15,outline=color,width=4)
        for x in (54,85): d.rounded_rectangle((x,43,x+21,63),radius=7,outline=color,width=3)
    elif harness == 'cursor':
        d.polygon([(57,25),(106,53),(84,61),(76,84)],fill=color)
        d.line((58,26,84,61,105,53),fill=(15,20,30),width=3)
    else:
        d.rounded_rectangle((47,27,113,81),radius=8,outline=color,width=4)
        d.line((59,43,70,54,59,65),fill=color,width=4)
        d.line((79,65,98,65),fill=color,width=4)
