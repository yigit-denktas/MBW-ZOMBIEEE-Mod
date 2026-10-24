from pathlib import Path


def _ops(row: str):
    tokens = row.split()
    count = int(tokens[3])
    cursor = 4
    for _ in range(count):
        argc = int(tokens[cursor + 1])
        cursor += 2 + argc
    n = int(tokens[cursor])
    cursor += 1
    ops = []
    for _ in range(n):
        op = int(tokens[cursor]); argc = int(tokens[cursor + 1]); cursor += 2
        args = tuple(int(v) for v in tokens[cursor:cursor + argc]); cursor += argc
        ops.append((op, args))
    return ops


def trigger_guard_diff(baseline_row: str, actual_row: str) -> bool:
    """True only for the authorised trigger-14 four-op log guard."""
    try:
        before = _ops(baseline_row)
        after = _ops(actual_row)
    except (ValueError, IndexError):
        return False
    if len(before) != 28 or len(after) != 28:
        return False
    if before[:24] != after[:24]:
        return False
    for op, args in before[24:]:
        if op != 502 or args != (-1, 200, 360287970189639680 + 873):
            return False
    for op, args in after[24:]:
        if (op != 502
                or args != (432345564227567616 + 16, 245,
                            360287970189639680 + 873)):
            return False
    return True


def original_prefix_ok(actual_rows, baseline_rows) -> bool:
    """Accept either the untouched original prefix or only the trigger-14 guard."""
    if len(actual_rows) < 25 or len(baseline_rows) < 25:
        return False
    if actual_rows[:25] == baseline_rows[:25]:
        return True
    return (all(actual_rows[i] == baseline_rows[i] for i in range(25) if i != 14)
            and trigger_guard_diff(baseline_rows[14], actual_rows[14]))
