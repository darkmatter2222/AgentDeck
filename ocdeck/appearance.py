"""Validated, hashable button preferences shared by the device and preview."""
from dataclasses import dataclass, fields
import math

THEMES = {
    'classic': ('20eb75', 'ffb32e', 'ff374b', '32ccff', 'ffb32e'),
    'aurora': ('59f3c2', 'd5a6ff', 'ff668f', '78bcff', 'e5c180'),
    'ocean': ('42e8c4', 'ffd280', 'ff7088', '69bfff', 'c4a7ff'),
    'accessible': ('56b4e9', 'e69f00', 'cc79a7', 'f0e442', 'ffffff'),
    'mono': ('ffffff', 'bbbbbb', 'ffffff', 'dddddd', '999999'),
}
HARNESS_NAMES = {'opencode': 'OpenCode', 'claude': 'Claude', 'copilot': 'Copilot',
                 'copilot-vscode': 'Copilot', 'gemini': 'Gemini', 'cursor': 'Cursor'}

@dataclass(frozen=True)
class Appearance:
    layout: str = 'classic'
    theme: str = 'classic'
    primary: str = 'status'
    secondary: str = 'project'
    custom_text: str = ''
    show_slot: bool = True
    effect: str = 'breathe'
    intensity: float = .55
    speed: float = 1.0
    brightness: float = 1.0


def appearance(config, slot=0):
    raw = config.get('appearance', {})
    if not isinstance(raw, dict): raise ValueError('appearance must be an object')
    overrides = config.get('buttons', {})
    if not isinstance(overrides, dict): raise ValueError('buttons must be an object')
    extra = overrides.get(str(slot + 1), {})
    if not isinstance(extra, dict): raise ValueError('button override must be an object')
    values = {**raw, **extra}
    unknown = set(values) - {f.name for f in fields(Appearance)}
    if unknown: raise ValueError('Unknown appearance setting: ' + ', '.join(sorted(unknown)))
    a = Appearance(**values)
    for name, choices in {'layout': ('classic','harness','minimal'), 'theme': THEMES,
                          'primary': ('status','project','harness','detail','custom','none'),
                          'secondary': ('status','project','harness','detail','custom','none'),
                          'effect': ('breathe','glow','steady')}.items():
        if getattr(a, name) not in choices: raise ValueError(f'Invalid {name}')
    for name, low, high in [('intensity',0,1),('speed',.25,3),('brightness',.15,1)]:
        value = getattr(a, name)
        if type(value) not in (int,float) or not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f'{name} must be {low}..{high}')
    if type(a.show_slot) is not bool: raise ValueError('show_slot must be boolean')
    if not isinstance(a.custom_text,str) or len(a.custom_text)>100: raise ValueError('custom_text must be at most 100 characters')
    return a


def harness_id(label, explicit=''):
    return explicit or (label.split(':',1)[0] if label.split(':',1)[0] in HARNESS_NAMES else 'opencode')


def animation_phase(now, a, enabled=True):
    return int(now * 48 * a.speed) % 96 if enabled and a.effect != 'steady' else 24
