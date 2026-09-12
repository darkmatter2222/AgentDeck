"""Regenerate README examples from the actual device renderer (no hardware needed)."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dataclasses import replace
from PIL import Image, ImageDraw, ImageFont
from ocdeck.art import frame
from ocdeck.appearance import Appearance, THEMES, animation_phase

OUT = Path(__file__).resolve().parents[1] / 'docs' / 'visuals'
OUT.mkdir(parents=True, exist_ok=True)
BG = '#101620'
FONT = ImageFont.load_default(size=16)
SMALL = ImageFont.load_default(size=12)
BASE = Appearance(layout='harness', theme='aurora', show_slot=False)
STATES = ['running','idle','input','unknown','ready','off']
HARNESSES = ['opencode','claude','copilot','copilot-vscode','gemini','cursor']


def panel(title, rows, phase=24):
    """Each row: name and (state, style, harness, label, caption) examples."""
    im = Image.new('RGB', (840, 60 + len(rows)*150), BG)
    d = ImageDraw.Draw(im)
    d.text((22,18), title, font=FONT, fill='white')
    for r, (name, examples) in enumerate(rows):
        y = 60 + r*150
        d.text((22,y+44), name, font=SMALL, fill='#a9b8cb')
        for k, (state, style, harness, label, caption) in enumerate(examples):
            x = 140 + k*114
            im.paste(frame(state,label,k,phase,100,style,harness,'Review changes'),(x,y))
            d.text((x+50,y+113),caption,font=SMALL,fill='#c6d2e3',anchor='mt')
    return im


def save(name, title, rows):
    panel(title,rows).save(OUT / (name+'.png'), optimize=True)


def row(style, states=STATES):
    return [(state,style,HARNESSES[k],'AgentDeck',state.upper()) for k,state in enumerate(states)]

save('layouts','THREE LAYOUTS / the same six states',[(name.title(),row(replace(BASE,layout=name))) for name in ['classic','harness','minimal']])
save('themes','FIVE PALETTES / consistent state labels',[(name.title(),row(replace(BASE,theme=name))) for name in THEMES])
save('harnesses','SIX ADAPTERS / one visual language',[('Harness',[( 'running',replace(BASE,primary='harness',secondary='status'),h,'AgentDeck',n) for h,n in zip(HARNESSES,['OpenCode','Claude','Copilot CLI','Copilot VS Code','Gemini','Cursor'])])])
text_options=[('status','project','State + project'),('project','status','Project + state'),('harness','status','Harness + state'),('detail','project','Detail + project'),('custom','status','Custom + state'),('none','none','Icon only')]
save('labels','CHOOSE WHAT GOES UNDER THE ICON',[('Text lines', [('running',replace(BASE,primary=p,secondary=s,custom_text='Code review'),'claude','HomeAILab',caption) for p,s,caption in text_options])])
save('brightness','PER-BUTTON DIMMING / rendered pixels, fixed device backlight',[('Brightness',[('running',replace(BASE,brightness=b),'gemini','AgentDeck',f'{int(b*100)}%') for b in [.15,.3,.45,.6,.8,1]])])
styles=[replace(BASE,theme='classic',primary='project',secondary='status'),replace(BASE,theme='ocean',primary='custom',custom_text='Code review'),replace(BASE,layout='minimal',theme='accessible'),replace(BASE,theme='aurora',primary='harness'),replace(BASE,theme='mono',effect='steady'),replace(BASE,theme='ocean',brightness=.6)]
save('mixed','MIX AND MATCH / six independent button styles',[('Per key',[(s,a,h,'HomeAILab',f'KEY {k+1}') for k,(s,a,h) in enumerate(zip(['running','input','idle','running','unknown','idle'],styles,HARNESSES))])])
# Compact, fixed-palette animated strips keep the README lightweight.
for name, title, specs in [
    ('effects','ANIMATION EFFECTS / same state, different motion', [(e,replace(BASE,layout='classic',effect=e,intensity=1),'input') for e in ['breathe','glow','steady']]),
    ('speeds','PULSE SPEED / slow, standard, fast', [(f'{v}x',replace(BASE,layout='classic',speed=v,intensity=1),'running') for v in [.5,1,2]])]:
    frames=[]
    for tick in range(96):
        im=Image.new('RGB',(510,210),BG); d=ImageDraw.Draw(im)
        d.text((18,15),title,font=SMALL,fill='white')
        for k,(caption,a,state) in enumerate(specs):
            im.paste(frame(state,'AgentDeck',k,animation_phase(tick/24,a),120,a,'claude'),(25+k*165,52))
            d.text((85+k*165,185),caption,font=SMALL,fill='white',anchor='mt')
        frames.append(im)
    palette = frames[0].quantize(colors=64)
    frames = [im.quantize(palette=palette,dither=Image.Dither.NONE) for im in frames]
    frames[0].save(OUT/(name+'.gif'),save_all=True,append_images=frames[1:],duration=[40,40,40,40,40,50]*16,loop=0,optimize=True)
print('\n'.join(f'{p.name}: {p.stat().st_size:,} bytes' for p in sorted(OUT.iterdir())))

# Extended customization examples, also drawn by the shipped renderer.
from ocdeck.appearance import PRESETS
save('presets','ONE-COMMAND PRESETS / real harness marks', [('Presets', [
    ('running',Appearance(**{**options,'alias':'My agent'}),h,'AgentDeck',name.title())
    for (name,options),h in zip(PRESETS.items(),HARNESSES)])])
save('details','SMALL DETAILS / make each key recognizable', [
    ('Badges', [('input',replace(BASE,badge=b),h,'AgentDeck',b.title()) for b,h in zip(['dot','ring','pill'],HARNESSES)]),
    ('Borders', [('running',replace(BASE,border=b),'gemini','AgentDeck',b.title()) for b in ['solid','double','corners','none']]),
    ('Backgrounds', [('idle',replace(BASE,background=b),'claude','AgentDeck',b.title()) for b in ['solid','gradient','grid']]),
    ('Logo size', [('running',replace(BASE,logo_size=b),'cursor','AgentDeck',b.title()) for b in ['small','normal','large']]),
])
save('typography','ALIASES AND TYPOGRAPHY / labels that work for you', [
    ('Alias', [('running',replace(BASE,alias=a,primary='alias',secondary='status'),'claude','AgentDeck',caption) for a,caption in [('Reviewer','Review agent'),('Builder','Build agent'),('Docs','Writing agent')]]),
    ('Text size', [('running',replace(BASE,text_size=b,alias='Builder'),'copilot','AgentDeck',b.title()) for b in ['small','normal','large']]),
    ('Alignment', [('idle',replace(BASE,text_align=b,alias='Docs'),'opencode','AgentDeck',b.title()) for b in ['left','center','right']]),
])
frames=[]
for tick in range(96):
    im=Image.new('RGB',(510,210),BG);d=ImageDraw.Draw(im)
    d.text((18,15),'TEXT EFFECTS / clipped scrolling and shimmer',font=SMALL,fill='white')
    for k,effect in enumerate(['none','scroll','shimmer']):
        a=replace(BASE,alias='Backend review agent',primary='alias',secondary='status',text_effect=effect,intensity=0)
        im.paste(frame('running','AgentDeck',k,tick,120,a,'claude'),(25+k*165,52))
        d.text((85+k*165,185),effect.upper(),font=SMALL,fill='white',anchor='mt')
    frames.append(im)
palette=frames[0].quantize(colors=96)
frames=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in frames]
frames[0].save(OUT/'text-effects.gif',save_all=True,append_images=frames[1:],duration=[80,80,80,80,80,100]*16,loop=0,optimize=True)
