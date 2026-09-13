"""Author the v3 hero with real runtime renderers. Requires Pillow and ffmpeg.

Run from the repository root: python scripts/preview_jelly_v3.py
24 seconds / 24 fps / 1280x720. Silent, seamless opening/closing composition.
The simulated device is deliberately labeled; no hardware-footage claim.
"""
from pathlib import Path
import math
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from ocdeck.jelly import Jelly, DeckGeometry
from ocdeck.art import frame as agent_frame
from ocdeck.appearance import Appearance

OUT = Path('docs/jelly')
FPS = 24
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

def font(size, bold=False):
    return ImageFont.truetype(BOLD if bold else FONT, size)

def background():
    im = Image.new('RGB', (1280, 720), '#080c17')
    glow = Image.new('RGB', im.size)
    d = ImageDraw.Draw(glow)
    d.ellipse((570, 110, 1170, 690), fill='#173440')
    d.ellipse((870, 0, 1330, 430), fill='#282246')
    glow = glow.filter(ImageFilter.GaussianBlur(110))
    from PIL import ImageChops
    im = ImageChops.add(im, glow)
    d = ImageDraw.Draw(im)
    d.text((64, 43), 'AGENTSTREAMDECK', font=font(18, True), fill='#e3e9f3')
    d.rounded_rectangle((1088, 35, 1216, 72), 18, fill='#163d3c', outline='#357c70')
    d.text((1152, 53), 'VERSION 3.0', anchor='mm', font=font(13, True), fill='#91efd0')
    d.line((64, 639, 1216, 639), fill='#334454')
    d.text((64, 666), 'A LITTLE LIFE.  RIGHT BESIDE YOUR CODE.', font=font(12, True), fill='#a1b6c8')
    d.text((1216, 666), 'OFFLINE  /  ON BY DEFAULT', anchor='ra', font=font(12), fill='#7bdfc1')
    return im

# Four editorial beats. Motion continues within each shot, with eased type reveals.
BEATS = [
    ('MEET YOUR CODING COMPANION', ['Make room', 'for Jelly.'], ['A tiny resident. A real personality.', 'Already at home on your Stream Deck.']),
    ('01  /  A HOME IN EVERY FREE KEY', ['Little button.', 'Big personality.'], ['Floor-level lounging. In-key exploring.', 'And a hop when adventure calls.']),
    ('02  /  IN SYNC WITH YOUR AGENTS', ['He notices.', 'He cares.'], ['An agent needs you? Jelly turns toward it.', 'Your controls always come first.']),
    ('03  /  A MIND OF HIS OWN', ['Code. Play.', 'Rest. Repeat.'], ['Colorful moods. Occasional little thoughts.', 'A companion for the rhythm of your work.']),
]

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    base = background()
    j = Jelly(DeckGeometry(), 7, 'fluid', {'needs': False, 'thoughts': 'off'})
    j.settle(3, 0)
    j.deadline = 100
    free = {1, 3, 4, 5}
    path = OUT / 'jelly_v3_showcase.mp4'
    proc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1280x720', '-r', str(FPS), '-i', '-', '-an', '-c:v', 'libx264', '-crf', '19', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(path)], stdin=subprocess.PIPE)
    events = {1: ('action','nod'), 3: ('action','dance'), 6: ('action','scoot'), 8: ('hop',4), 11: ('action','edge_peek'), 12: ('mood','attentive'), 13: ('action','point_right'), 15: ('action','nod'), 17: ('mood','proud'), 17.5: ('action','cheer'), 20: ('thought','quiet'), 22: ('mood','content')}
    for i in range(FPS * 24):
        t = i / FPS
        if t in events:
            kind, value = events[t]
            if kind == 'action': j.start_action(value, t, target=2)
            elif kind == 'hop': j.hop(value, t, free)
            elif kind == 'mood': j.mind.set_mood(value, t, hold=30)
            else:
                j.thoughts.frequency = 'chatty'
                j.thoughts.next_at = t
                j.thoughts.say(value, t)
        j.update(t, free)
        # Author quiet holds between actions, without random cuts or teleports.
        if j.state == 'idle': j.deadline = 100
        im = base.copy()
        d = ImageDraw.Draw(im)
        beat = min(3, int(t // 6))
        label, title, copy = BEATS[beat]
        progress = min(1, (t % 6) / .55)
        shift = round(12 * (1-progress)**3)
        d.text((64, 180+shift), label, font=font(12, True), fill='#7bdfc1')
        for n, line in enumerate(title): d.text((60, 219+n*66+shift), line, font=font(52, True), fill='#f3f5fc')
        for n, line in enumerate(copy): d.text((64, 391+n*28+shift), line, font=font(16), fill='#aebdd0')
        for n in range(4):
            x=64+n*52
            d.rounded_rectangle((x, 487, x+38, 490), 2, fill='#75e3c2' if n == beat else '#354358')
        # Precision front view: each LCD is a viewport into the same deck space.
        # The bezel masks the crossing sprite exactly as physical separate keys do.
        x, y = 620, 176
        d.rounded_rectangle((x-18,y-18,x+578,y+402), 48, fill='#060910')
        d.rounded_rectangle((x-18,y-28,x+578,y+380), 46, fill='#343c48', outline='#586472', width=2)
        d.rounded_rectangle((x-14,y-24,x+574,y+374), 43, fill='#151c26')
        d.text((x+280,y-6), 'STREAM DECK', font=font(12, True), anchor='mt', fill='#8d99a8')
        crops = j.crops(free)
        for key in range(6):
            col, row = key % 3, key // 3
            kx, ky = x+24+col*176, y+34+row*176
            d.rounded_rectangle((kx-7,ky-7,kx+166,ky+166), 19, fill='#05070c', outline='#404956', width=2)
            if key in (0,2):
                state = 'input' if key == 2 and 12 <= t < 17 else 'idle' if key == 2 and t >= 17 else 'running'
                lcd = agent_frame(state, 'API' if key == 0 else 'APP', key, i%96, style=Appearance(layout='harness'), harness='opencode' if key == 0 else 'claude').resize((160,160), Image.Resampling.LANCZOS)
            else:
                lcd = Image.new('RGB',(80,80),'black')
                if key in crops: lcd.paste(crops[key],(0,0),crops[key])
                lcd = lcd.resize((160,160), Image.Resampling.NEAREST)
            mask = Image.new('L',(160,160)); ImageDraw.Draw(mask).rounded_rectangle((0,0,159,159),12,fill=255)
            im.paste(lcd,(kx,ky),mask)
        d.text((900,604), 'ACTUAL RUNTIME ART  /  SIMULATED MINI', font=font(10), anchor='mm', fill='#8198a9')
        # Gentle dip to the opening creates a comfortable looping README hero.
        if t > 23.3:
            im = Image.blend(im, first, min(1,(t-23.3)/.65))
        if i == 0: first = im.copy()
        if i == 4*FPS: im.save(OUT/'jelly_v3_poster.png')
        proc.stdin.write(im.tobytes())
    proc.stdin.close()
    if proc.wait(): raise RuntimeError('Video encoding failed')
    subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(path),'-filter_complex','fps=16,scale=960:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=3','-loop','0',str(OUT/'jelly_v3_showcase.gif')],check=True)
    print(path)

if __name__ == '__main__':
    main()
