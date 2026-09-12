"""Device artwork with bundled, attributed official harness icons."""
import math
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageChops
from .appearance import Appearance, THEMES, HARNESS_NAMES
from pathlib import Path

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
    draw_background(d, color, c, style)
    if style.layout == "harness" and state != "ready":
        logo = harness_logo(harness, {'small':42, 'normal':56, 'large':68}[style.logo_size])
        if logo is not None:
            im.paste(logo, (80-logo.width//2, 54-logo.height//2), logo)
        else:
            # Unknown integrations get a neutral terminal, never another brand.
            d.rounded_rectangle((52,32,108,76),radius=6,outline=color,width=3)
            d.text((80,54),'?',font=ImageFont.load_default(size=26),fill=color,anchor='mm')
        draw_badge(d, state, c, style.badge)
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
    project = style.alias or project
    values = {'status': LABELS[state], 'project': 'DEVICE ONLINE' if state == 'ready' else project,
              'alias': 'DEVICE ONLINE' if state == 'ready' else project,
              'harness': HARNESS_NAMES.get(harness, harness), 'detail': detail,
              'custom': style.custom_text, 'none': ''}
    for field, y, height, fill in [(style.primary, 101, 17, color), (style.secondary, 130, 13, (210,219,228))]:
        text = values[field]
        if style.show_slot and field in ('project','alias') and state != 'ready': text = f'{slot+1}  {text}'
        render_text(im, text, y, height, fill, style, phase)
    im = im.resize((size, size), Image.Resampling.LANCZOS)
    gain = style.brightness * (1 - style.intensity * .22 * (1 - pulse) if style.effect == 'glow' else 1)
    return ImageEnhance.Brightness(im).enhance(gain) if gain != 1 else im


@lru_cache(maxsize=32)
def harness_logo(harness, size):
    canonical = {'copilot-cli':'copilot', 'copilot-vscode':'copilot'}.get(harness,harness)
    if canonical not in ('opencode','claude','copilot','gemini','cursor'):
        return None
    path = Path(__file__).parent / 'assets' / 'logos' / (canonical + '.png')
    with Image.open(path) as source:
        image = source.convert('RGBA')
    image.thumbnail((size,size),Image.Resampling.LANCZOS)
    return image


def draw_background(d, color, pulse_color, style):
    base = tuple(int(x*.08) for x in pulse_color)
    d.rounded_rectangle((3,3,156,156),radius=22,fill=base)
    if style.background == 'gradient':
        for y in range(16,145):
            gain = .03 + .13 * (1-abs(y-80)/65)
            d.line((14,y,145,y),fill=tuple(int(x*gain) for x in color))
    elif style.background == 'grid':
        grid = tuple(int(x*.14) for x in color)
        for pos in range(20,145,16):
            d.line((pos,12,pos,147),fill=grid)
            d.line((12,pos,147,pos),fill=grid)
    if style.border in ('solid','double'):
        d.rounded_rectangle((3,3,156,156),radius=22,outline=pulse_color,width=3)
        if style.border == 'double':
            d.rounded_rectangle((9,9,150,150),radius=17,outline=tuple(int(x*.45) for x in color),width=1)
    elif style.border == 'corners':
        for x,y,dx,dy in [(8,8,1,1),(151,8,-1,1),(8,151,1,-1),(151,151,-1,-1)]:
            d.line((x+dx*24,y,x,y,x,y+dy*24),fill=pulse_color,width=3)


def draw_badge(d,state,color,kind):
    symbol = {'running':'>','idle':'II','input':'!','unknown':'?'}[state]
    if kind == 'pill':
        d.rounded_rectangle((111,10,150,30),radius=7,fill=color)
        label = {'running':'RUN','idle':'IDLE','input':'ASK','unknown':'?'}[state]
        d.text((131,20),label,font=ImageFont.load_default(size=10),fill='black',anchor='mm')
    elif kind == 'ring':
        d.ellipse((125,10,149,34),outline=color,width=3)
        d.text((137,22),symbol,font=ImageFont.load_default(size=11),fill='white',anchor='mm')
    else:
        d.ellipse((128,13,147,32),fill=color,outline='white',width=2)


def render_text(image, text, y, height, fill, style, phase):
    if not text: return
    text = text.encode('ascii','replace').decode()
    height += {'small':-2,'normal':0,'large':3}[style.text_size]
    font = ImageFont.load_default(size=height)
    layer = Image.new('RGBA',(140,28))
    d = ImageDraw.Draw(layer)
    width = d.textlength(text,font=font)
    if style.text_effect == 'scroll' and width > 140:
        # Ping-pong scroll with an endpoint pause, clipped to its own text line.
        t = (phase % 96)/96
        progress = max(0,min(1,(t-.1)/.3)) if t < .5 else 1-max(0,min(1,(t-.6)/.3))
        progress = (1-math.cos(progress*math.pi))/2
        x = -(width-140)*progress
    else:
        if width > 140:
            lo,hi=0,len(text)
            while lo<hi:
                mid=(lo+hi+1)//2
                if d.textlength(text[:mid]+'...',font=font)<=140: lo=mid
                else: hi=mid-1
            text=text[:lo]+'...'
            width=d.textlength(text,font=font)
        x={'left':0,'center':(140-width)/2,'right':140-width}[style.text_align]
    d.text((x,14),text,font=font,fill=fill,anchor='lm')
    if style.text_effect == 'shimmer':
        shine=Image.new('RGBA',layer.size,'white')
        mask=Image.new('L',layer.size); m=ImageDraw.Draw(mask)
        center=-30+(phase%96)/96*200
        for col in range(140):
            m.line((col,0,col,27),fill=int(180*max(0,1-abs(col-center)/22)))
        shine.putalpha(ImageChops.multiply(mask,layer.getchannel('A')))
        layer=Image.alpha_composite(layer,shine)
    image.paste(layer,(10,y-14),layer)
