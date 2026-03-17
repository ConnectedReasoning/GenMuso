#!/usr/bin/env python3
"""
main.py — GenMuso2: Generative Music Engine

Usage:
    python main.py passion                       # built-in preset
    python main.py focus --seed 42               # reproducible generation
    python main.py compositions/my_piece.json    # your own JSON composition
    python main.py --list                        # show available presets
"""

import argparse
import sys
import os

from presets import PRESETS
from loader import load_json
from generator import generate


def main():
    parser = argparse.ArgumentParser(
        description='GenMuso2 — Generative Music Engine',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Presets: ' + ', '.join(PRESETS.keys()),
    )
    parser.add_argument(
        'source', nargs='?', default=None,
        help='Preset name OR path to a .json composition file',
    )
    parser.add_argument(
        '--seed', type=int, default=None,
        help='Random seed for reproducible output',
    )
    parser.add_argument(
        '--output', '-o', type=str, default=None,
        help='Output file path (default: auto-generated)',
    )
    parser.add_argument(
        '--list', action='store_true',
        help='List available presets and exit',
    )
    parser.add_argument(
        '--info', action='store_true',
        help='Show preset details without generating',
    )

    args = parser.parse_args()

    if args.list:
        print('\nAvailable presets:')
        for name, factory in PRESETS.items():
            comp = factory()
            print(f'  {name:<12s}  {len(comp.sections):>3d} sections, '
                  f'{comp.total_bars:>4d} bars')
        print()
        return

    if args.source is None:
        parser.print_help()
        return

    # Decide: JSON file or preset name?
    if args.source.endswith('.json'):
        if not os.path.exists(args.source):
            print(f"\nFile not found: {args.source}")
            sys.exit(1)
        comp = load_json(args.source)
    elif args.source in PRESETS:
        comp = PRESETS[args.source]()
    else:
        print(f"\nUnknown preset: '{args.source}'")
        print(f'Available presets: {", ".join(PRESETS.keys())}')
        print(f'Or pass a path to a .json file.')
        sys.exit(1)

    print(f'\n{"="*60}')
    print(f'  GenMuso2 — {comp.name}')
    print(f'{"="*60}')

    if args.info:
        print(comp.summary())
        return

    print(comp.summary())
    print(f'\nGenerating...')

    # Generate
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    output_path = args.output or os.path.join(output_dir, f'{comp.name}.mid')

    path = generate(comp, output_path=output_path, seed=args.seed)
    print(f'\nDone. Open {path} in your DAW.\n')


if __name__ == '__main__':
    main()
