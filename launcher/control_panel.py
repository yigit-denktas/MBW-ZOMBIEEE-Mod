"""Minimal desktop control panel: Play Solo, settings, logs, repair, release.

The pure ``actions`` function is importable and testable without a GUI. The
Tk window is created lazily in ``main`` and only starts the launcher's own
commands as separate child processes; it never launches a game directly and
never blocks the launcher's safety checks.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys

SCHEMA = 'zombieee.control-panel.v1'
ACTIONS = ('play', 'settings', 'logs', 'repair', 'uninstall', 'release')


def _launcher_argv(module, *arguments):
    return [sys.executable, '-m', module, *[str(item) for item in arguments]]


def actions(*, settings_path=None, evidence_root=None):
    """Return the control-panel action list without starting anything."""
    settings_args = (['--settings', str(settings_path)]
                     if settings_path is not None else [])
    base = _launcher_argv('launcher.play_city')
    result = [
        {'id': 'play', 'label': 'Play Solo City',
         'command': base + ['play', *settings_args]},
        {'id': 'settings', 'label': 'Settings / profile matrix',
         'command': base + ['matrix', *settings_args]},
        {'id': 'logs', 'label': 'Open evidence / logs',
         'command': base + ['logs', *settings_args]},
        {'id': 'repair', 'label': 'Verify and repair install',
         'command': base + ['verify', *settings_args]},
        {'id': 'uninstall', 'label': 'Uninstall (quarantine, no deletion)',
         'command': base + ['uninstall', *settings_args]},
        {'id': 'release', 'label': 'Release/delivery checks',
         'command': _launcher_argv('launcher.release_gate')},
    ]
    if evidence_root is not None:
        for entry in result:
            if entry['id'] == 'logs':
                entry['evidence_root'] = str(evidence_root)
    return result


def format_actions(action_list):
    lines = ['ZOMBIEEE control panel actions:']
    for entry in action_list:
        lines.append('  %-10s %s' % (entry['id'], entry['label']))
        lines.append('             ' + ' '.join(entry['command']))
    return '\n'.join(lines)


def _run_action(entry):
    try:
        subprocess.Popen(entry['command'], shell=False)
    except OSError:
        pass


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--print-actions', action='store_true',
                        help='print the menu actions; never opens a window')
    parser.add_argument('--json', action='store_true', help='emit JSON')
    parser.add_argument('--settings', help='private launcher settings JSON path')
    parser.add_argument('--evidence-root', help='private evidence directory')
    args = parser.parse_args(argv)
    action_list = actions(settings_path=args.settings,
                          evidence_root=args.evidence_root)
    if args.print_actions or args.json:
        if args.json:
            print(json.dumps({'schema': SCHEMA, 'schema_version': 1,
                              'actions': action_list,
                              'runtime_verified': False}, indent=2,
                             sort_keys=True))
        else:
            print(format_actions(action_list))
        return 0
    try:
        import tkinter as tk
        from tkinter import messagebox
    except ImportError:
        print(format_actions(action_list))
        return 2
    window = tk.Tk()
    window.title('ZOMBIEEE City - private local launcher')

    def make_handler(entry):
        def handler():
            _run_action(entry)
        return handler

    tk.Label(window, text='Private local City launcher').pack(padx=12, pady=8)
    for entry in action_list:
        tk.Button(window, text=entry['label'], width=42,
                  command=make_handler(entry)).pack(padx=12, pady=3)
    tk.Label(window, text='Actions start the documented CLI; no game is '
                          'launched without its safety checks.').pack(padx=12,
                                                                    pady=8)
    window.mainloop()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
