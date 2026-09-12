import argparse
import json
from pathlib import Path
import sys
from .common import home, identity, request


def main():
    parser = argparse.ArgumentParser(prog='ocdeck')
    sub = parser.add_subparsers(dest='command', required=True)
    broker = sub.add_parser('broker'); broker.add_argument('--mock', action='store_true')
    sub.add_parser('status'); sub.add_parser('stop'); sub.add_parser('devices')
    sub.add_parser('hardware-check')
    launch = sub.add_parser('launch'); launch.add_argument('args', nargs=argparse.REMAINDER)
    route = sub.add_parser('route'); route.add_argument('args', nargs=argparse.REMAINDER)
    worker = sub.add_parser('worker'); worker.add_argument('spec')
    ident = sub.add_parser('identity'); ident.add_argument('pid', type=int)
    plug = sub.add_parser('install-plugin'); plug.add_argument('--mode', choices=['server', 'tui'], default='server'); plug.add_argument('--config-dir')
    from .harness import PROFILES
    hp = sub.add_parser('harness-install')
    hp.add_argument('profile', choices=PROFILES); hp.add_argument('--project', default='.')
    hp.add_argument('--remove', action='store_true'); hp.add_argument('--dry-run', action='store_true')
    hl = sub.add_parser('harness-launch')
    hl.add_argument('--profile', required=True, choices=PROFILES); hl.add_argument('--executable')
    hl.add_argument('--current-window', action='store_true'); hl.add_argument('args', nargs=argparse.REMAINDER)
    hw = sub.add_parser('harness-worker'); hw.add_argument('spec')
    preview = sub.add_parser('preview'); preview.add_argument('--output', default='animation-preview.gif')
    from .appearance import THEMES, PRESETS
    customize = sub.add_parser('appearance', help='Save button appearance; restart broker to apply')
    customize.add_argument('--slot', type=int, choices=range(1,7))
    for target in (customize, preview):
        target.add_argument('--preset', choices=list(PRESETS))
        target.add_argument('--alias')
        for name, choices in {
            'text-effect': ['none','scroll','shimmer'], 'text-size': ['small','normal','large'],
            'text-align': ['left','center','right'], 'badge': ['dot','ring','pill'],
            'border': ['solid','double','corners','none'],
            'background': ['solid','gradient','grid'], 'logo-size': ['small','normal','large'],
        }.items():
            target.add_argument('--'+name, choices=choices)
        target.add_argument('--layout', choices=['classic','harness','minimal'])
        target.add_argument('--theme', choices=list(THEMES))
        target.add_argument('--effect', choices=['breathe','glow','steady'])
        for name in ('primary','secondary'):
            target.add_argument('--' + name, choices=['status','project','harness','detail','custom','alias','none'])
        target.add_argument('--custom-text')
        target.add_argument('--show-slot', action=argparse.BooleanOptionalAction, default=None)
        target.add_argument('--speed', type=float)
        target.add_argument('--intensity', type=float)
        target.add_argument('--brightness', type=float, help='Per-button image brightness, 0.15..1')
    customize.add_argument('--fps', type=int, choices=range(1,31))
    focus = sub.add_parser('focus'); focus.add_argument('slot', type=int)
    args = parser.parse_args()
    try:
        if args.command == 'broker':
            from .broker import run
            run(mock=args.mock)
        elif args.command in ('status', 'stop'):
            print(json.dumps(request('GET' if args.command == 'status' else 'POST', '/v1/' + args.command), indent=2))
        elif args.command == 'identity': print(json.dumps(identity(args.pid)))
        elif args.command == 'launch':
            from .launcher import launch
            launch(args.args[1:] if args.args[:1] == ['--'] else args.args)
        elif args.command == 'route':
            from .launcher import route
            return route(args.args[1:] if args.args[:1] == ['--'] else args.args)
        elif args.command == 'worker':
            from .launcher import worker
            return worker(args.spec)
        elif args.command == 'install-plugin':
            from .launcher import install_plugin
            install_plugin(args.mode, args.config_dir)
        elif args.command == 'harness-install':
            from .harness import install
            return install(args.profile, args.project, args.remove, args.dry_run)
        elif args.command == 'harness-launch':
            from .harness import launch
            return launch(args.profile, args.args[1:] if args.args[:1] == ['--'] else args.args,
                          args.executable, args.current_window)
        elif args.command == 'harness-worker':
            from .harness import worker
            return worker(args.spec)
        elif args.command == 'devices':
            from .device import enumerate_minis
            print(json.dumps([{k: (v.decode(errors='replace') if isinstance(v, bytes) else v)
                               for k, v in d.items()} for d in enumerate_minis()], indent=2))
        elif args.command == 'hardware-check':
            from .hardware_check import run
            run()
        elif args.command == 'focus':
            if not 1 <= args.slot <= 6: raise ValueError('Slot must be 1..6')
            view = request('GET', '/v1/status')['slots'][args.slot - 1]
            print(json.dumps(request('POST', '/v1/focus', view), indent=2))
        elif args.command == 'appearance':
            from .appearance import Appearance, appearance, animation_phase
            from dataclasses import fields, asdict
            from .common import read_json, atomic_json
            config = read_json(home() / 'config.json') if (home() / 'config.json').exists() else {}
            if not isinstance(config, dict): raise ValueError('config.json must contain an object')
            changes = {f.name: getattr(args, f.name) for f in fields(Appearance) if getattr(args, f.name) is not None}
            if args.preset:
                preset = asdict(Appearance(**PRESETS[args.preset]))
                # Applying a visual preset should not erase the user's labels.
                preset.pop('alias'); preset.pop('custom_text')
                changes = {**preset, **changes}
            if changes:
                target = config.setdefault('appearance', {}) if args.slot is None else config.setdefault('buttons', {}).setdefault(str(args.slot), {})
                target.update(changes)
            if args.fps is not None: config['fps'] = args.fps
            for slot in range(6): appearance(config, slot)
            if changes or args.fps is not None:
                atomic_json(home() / 'config.json', config)
                print('Appearance saved. Restart the AgentDeck broker to apply.')
            print(json.dumps(config, indent=2))
        elif args.command == 'preview':
            from .art import frame
            from PIL import Image, ImageDraw
            from .appearance import Appearance, appearance, animation_phase
            from .common import read_json
            from dataclasses import fields, asdict
            config = read_json(home() / 'config.json') if (home() / 'config.json').exists() else {} or {}
            changes = {f.name: getattr(args, f.name) for f in fields(Appearance) if getattr(args, f.name) is not None}
            if args.preset:
                preset = asdict(Appearance(**PRESETS[args.preset]))
                # Applying a visual preset should not erase the user's labels.
                preset.pop('alias'); preset.pop('custom_text')
                changes = {**preset, **changes}
            config['appearance'] = {**config.get('appearance', {}), **changes}
            # Explicit preview flags override saved per-button preferences.
            styles = [appearance({'appearance': {**config.get('appearance', {}), **config.get('buttons', {}).get(str(k+1), {}), **changes}}, k) for k in range(6)]
            images = []
            states = ['running', 'idle', 'input', 'running', 'unknown', 'ready']
            count = min(192, max(48, round(48 / min(style.speed for style in styles))))
            for phase in range(count):
                im = Image.new('RGB', (532, 370), '#10141d')
                d = ImageDraw.Draw(im)
                d.text((22, 12), 'AGENTDECK / APPEARANCE PREVIEW', fill='white')
                for k, state in enumerate(states):
                    im.paste(frame(state, 'HomeAILab', k, animation_phase(phase/24, styles[k], config.get('animations', True)), 150, styles[k], ['opencode','claude','copilot','gemini','cursor','opencode'][k], 'Review changes'), (22 + (k % 3)*170, 40 + (k // 3)*160))
                images.append(im)
            images[0].save(args.output, save_all=True, append_images=images[1:], duration=[50 if n%6 == 5 else 40 for n in range(count)], loop=0)
            print(str(Path(args.output).resolve()))
    except Exception as error:
        print(f'ocdeck: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
