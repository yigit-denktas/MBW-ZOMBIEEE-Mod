"""Read-only, bounded Warband/WSE2 discovery. Never executes a candidate.

Run from the repository root: python -m launcher.discovery --help
PE presence and Steam manifests do not establish a licence or compatibility.
"""
import argparse
import json
import os
import re
import struct
from pathlib import Path


def read_vdf(path):
    """Parse the quoted strings/braces subset used by Steam, fail on damage."""
    with path.open('r', encoding='utf-8-sig') as handle:
        text = handle.read(1024 * 1024 + 1)
    if len(text) > 1024 * 1024:
        raise ValueError('VDF size limit exceeded')
    tokens = []
    pattern = re.compile(r'\s+|//[^\n]*|"((?:\\.|[^"\\])*)"|([{}])')
    pos = 0
    while pos < len(text):
        match = pattern.match(text, pos)
        if not match:
            raise ValueError('unsupported or malformed VDF')
        if match.group(1) is not None:
            value = re.sub(r'\\([\\"])', r'\1', match.group(1))
            tokens.append(('string', value))
        elif match.group(2):
            tokens.append((match.group(2), match.group(2)))
        pos = match.end()
    index = 0

    def obj(nested=False, depth=0):
        nonlocal index
        if depth > 16:
            raise ValueError('VDF nesting limit exceeded')
        result = {}
        while index < len(tokens):
            kind, key = tokens[index]
            index += 1
            if kind == '}' and nested:
                return result
            if kind != 'string' or index == len(tokens):
                raise ValueError('missing VDF key/value')
            kind, value = tokens[index]
            index += 1
            if kind == '{':
                value = obj(True, depth + 1)
            elif kind != 'string':
                raise ValueError('invalid VDF value')
            key = key.casefold()
            if key in result:
                raise ValueError('duplicate VDF key')
            result[key] = value
        if nested:
            raise ValueError('unterminated VDF object')
        return result
    return obj()


def executable_status(path):
    """Only a PE header sanity check, not executable integrity validation."""
    try:
        with path.open('rb') as handle:
            header = handle.read(64)
            if len(header) != 64 or header[:2] != b'MZ':
                return 'invalid_pe_header'
            offset = struct.unpack_from('<I', header, 60)[0]
            if offset < 64 or offset > 16 * 1024 * 1024:
                return 'invalid_pe_header'
            handle.seek(offset)
            if handle.read(4) != b'PE\0\0':
                return 'invalid_pe_header'
    except FileNotFoundError:
        return 'missing_executable'
    except ValueError:
        # Python 3.13 raises ValueError for an embedded NUL in a path on open()
        # (older versions may surface OSError). A malformed candidate is data,
        # never a reason to abort the whole bounded discovery report.
        return 'invalid_path'
    except OSError:
        return 'unreadable_executable'
    return 'found'


def file_version(path):
    """Read Windows fixed version metadata as data; unknown stays None.

    The resource may be absent, stale or describe an underlying engine rather
    than WSE2. This is not a compatibility verdict or a launched-engine version.
    """
    if os.name != 'nt':
        return None
    import ctypes
    from ctypes import wintypes
    api = ctypes.WinDLL('version', use_last_error=True)
    api.GetFileVersionInfoSizeW.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(wintypes.DWORD)]
    api.GetFileVersionInfoSizeW.restype = wintypes.DWORD
    api.GetFileVersionInfoW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p]
    api.GetFileVersionInfoW.restype = wintypes.BOOL
    api.VerQueryValueW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR,
                                 ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(wintypes.UINT)]
    api.VerQueryValueW.restype = wintypes.BOOL
    ignored = wintypes.DWORD()
    size = api.GetFileVersionInfoSizeW(str(path), ctypes.byref(ignored))
    if not size or size > 1024 * 1024:
        return None
    buffer = ctypes.create_string_buffer(size)
    if not api.GetFileVersionInfoW(str(path), 0, size, buffer):
        return None
    pointer, length = ctypes.c_void_p(), wintypes.UINT()
    if not api.VerQueryValueW(buffer, '\\', ctypes.byref(pointer), ctypes.byref(length)) or length.value < 52:
        return None
    values = ctypes.cast(pointer, ctypes.POINTER(wintypes.DWORD))
    if values[0] != 0xFEEF04BD:
        return None
    high, low = values[2], values[3]
    return '.'.join(str(v) for v in (high >> 16, high & 0xffff, low >> 16, low & 0xffff))


def known_locations(environ=None):
    """Use environment-derived folders and optional Steam registry hints."""
    env = os.environ if environ is None else environ
    steam, games = [], []
    for key in ('ProgramFiles(x86)', 'ProgramFiles', 'ProgramW6432'):
        if env.get(key):
            base = Path(env[key])
            steam.append(base / 'Steam')
            games.extend((base / 'MountBlade Warband', base / 'Mount&Blade Warband'))
    if os.name == 'nt' and environ is None:
        import winreg
        # Steam hints only; WSE2 has no assumed registry location.
        for hive, key, value in (
            (winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam', 'SteamPath'),
            (winreg.HKEY_LOCAL_MACHINE, r'Software\Valve\Steam', 'InstallPath'),
            (winreg.HKEY_LOCAL_MACHINE, r'Software\WOW6432Node\Valve\Steam', 'InstallPath'),
        ):
            try:
                with winreg.OpenKey(hive, key) as handle:
                    steam.append(Path(winreg.QueryValueEx(handle, value)[0]))
            except OSError:
                pass
    return steam, games


def discover(steam_roots=(), custom_paths=(), known_roots=()):
    """Explicit inputs make fixtures independent of the user's machine.

    CLI adds known_locations(); direct API never scans implicitly. Custom
    paths may name game/WSE2 directories or executables. WSE2 search is limited
    to three directory levels and 512 entries per root; links are skipped.
    """
    warnings, games, wse, libraries, search = [], {}, {}, {}, {}

    def add(table, path, provenance):
        try:
            path = Path(path).expanduser().resolve()
        except (OSError, RuntimeError, ValueError) as exc:
            warnings.append({'source': str(path), 'reason': type(exc).__name__})
            return
        key = os.path.normcase(str(path))
        if key not in table:
            table[key] = (path, [])
        if provenance not in table[key][1]:
            table[key][1].append(provenance)

    def vdf(path):
        try:
            # Absent optional manifests are ordinary; corrupt/unreadable are evidence.
            if not path.exists():
                return {}
            return read_vdf(path)
        except (OSError, ValueError, RecursionError) as exc:
            warnings.append({'source': str(path), 'reason': type(exc).__name__})
            return {}

    for root in steam_roots:
        try:
            root = Path(root).expanduser().resolve()
        except (OSError, RuntimeError, ValueError) as exc:
            warnings.append({'source': str(root), 'reason': type(exc).__name__})
            continue
        add(libraries, root, 'steam_root:' + str(root))
        folders = vdf(root / 'steamapps/libraryfolders.vdf').get('libraryfolders', {})
        if not isinstance(folders, dict):
            warnings.append({'source': str(root), 'reason': 'invalid_libraryfolders'})
            continue
        for key, value in folders.items():
            if key.isdigit():
                path = value.get('path') if isinstance(value, dict) else value
                if isinstance(path, str) and Path(path).is_absolute():
                    add(libraries, path, 'steam_libraryfolders:' + str(root))
                else:
                    warnings.append({'source': str(root), 'reason': 'invalid_library_path'})
    for root, provenance in libraries.values():
        manifest_path = root / 'steamapps/appmanifest_48700.acf'
        manifest = vdf(manifest_path).get('appstate', {})
        name = manifest.get('installdir') if isinstance(manifest, dict) else None
        if name is not None:
            if (not isinstance(name, str) or not name or name in ('.', '..')
                    or any(c in name for c in '/\\:<>"|?*')
                    or any(ord(c) < 32 for c in name)
                    or str(manifest.get('appid')) != '48700'):
                warnings.append({'source': str(manifest_path), 'reason': 'unsafe_or_invalid_appmanifest'})
            else:
                add(games, root / 'steamapps/common' / name, 'steam_manifest:' + str(manifest_path))
        default = root / 'steamapps/common/MountBlade Warband'
        if default.is_dir():
            add(games, default, 'steam_known_folder:' + str(root))
    for root in known_roots:
        if Path(root).is_dir():
            add(games, root, 'known_folder:' + str(root))
    for custom in custom_paths:
        custom = Path(custom).expanduser()
        if custom.suffix.casefold() == '.exe':
            if custom.name.casefold() == 'mb_warband.exe':
                add(games, custom.parent, 'custom:' + str(custom))
            elif 'wse2' in custom.name.casefold():
                add(wse, custom, 'custom:' + str(custom))
            else:
                warnings.append({'source': str(custom), 'reason': 'unrecognized_executable_name'})
        else:
            add(games, custom, 'custom:' + str(custom))
            add(search, custom, 'custom_search:' + str(custom))
    for root, provenance in games.values():
        add(search, root, provenance[0])
    for root, provenance in search.values():
        pending, budget = [(root, 0)], 512
        while pending and budget > 0:
            folder, depth = pending.pop()
            try:
                with os.scandir(folder) as entries:
                    for entry in entries:
                        budget -= 1
                        if budget < 0:
                            break
                        path = Path(entry.path)
                        # is_symlink alone does not cover Windows directory junctions.
                        attrs = entry.stat(follow_symlinks=False).st_file_attributes if os.name == 'nt' else 0
                        if entry.is_symlink() or attrs & 0x400:
                            continue
                        if entry.is_dir(follow_symlinks=False) and depth < 3:
                            pending.append((path, depth + 1))
                        elif entry.is_file(follow_symlinks=False) and path.suffix.casefold() == '.exe' and 'wse2' in path.name.casefold():
                            add(wse, path, 'bounded_search:' + str(root))
            except FileNotFoundError:
                pass
            except (OSError, ValueError) as exc:
                # A malformed configured path (for example an embedded NUL) can
                # raise ValueError from scandir on Python 3.13; keep the bounded
                # report structured instead of aborting discovery entirely.
                warnings.append({'source': str(folder), 'reason': type(exc).__name__})
        if pending or budget <= 0:
            warnings.append({'source': str(root), 'reason': 'search_limit_reached'})

    def candidate(path, provenance, kind):
        exe = path / 'mb_warband.exe' if kind == 'warband' else path
        status = executable_status(exe)
        version = file_version(exe) if status == 'found' else None
        return {'path': str(path), 'executable': str(exe), 'kind': kind,
                'status': status, 'confidence': 'medium' if status == 'found' else 'none',
                'engine_version': version,
                'version_status': 'file_resource_only' if version else 'unknown',
                'ownership': 'unknown', 'runtime_verified': False,
                'provenance': provenance,
                'blockers': [] if status == 'found' else [status]}

    candidates = [candidate(p, sources, 'warband') for p, sources in games.values()]
    wse_candidates = [candidate(p, sources, 'wse2') for p, sources in wse.values()]
    found = [c for c in candidates if c['status'] == 'found']
    found_wse = [c for c in wse_candidates if c['status'] == 'found']
    blockers = []
    if not found:
        blockers.append('warband_not_found')
    if not found_wse:
        blockers.append('wse2_not_found')
    if len(found) > 1 or len(found_wse) > 1:
        blockers.append('selection_required')
    return {'schema_version': 1, 'read_only': True, 'candidates': candidates,
            'wse2_candidates': wse_candidates, 'ambiguity': len(found) > 1 or len(found_wse) > 1,
            'selected': found[0]['path'] if len(found) == 1 else None,
            'blockers': blockers, 'warnings': warnings}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--steam-root', action='append', default=[])
    parser.add_argument('--custom-path', action='append', default=[])
    parser.add_argument('--no-known-folders', action='store_true')
    args = parser.parse_args()
    steam, games = ([], []) if args.no_known_folders else known_locations()
    report = discover([*steam, *args.steam_root], args.custom_path, games)
    print(json.dumps(report, indent=2))
    return 0 if report['selected'] and not report['ambiguity'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
