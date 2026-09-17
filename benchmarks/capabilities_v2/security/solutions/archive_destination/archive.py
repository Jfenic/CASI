from pathlib import Path, PurePosixPath


def destination(base, member):
    root = Path(base).resolve()
    name = PurePosixPath(member)
    if not member or name.is_absolute() or ".." in name.parts:
        raise ValueError("invalid archive path")
    target = (root / member).resolve()
    if not target.is_relative_to(root):
        raise ValueError("outside base")
    return target
