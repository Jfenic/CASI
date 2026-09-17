from pathlib import Path


def destination(base, member):
    return (Path(base) / member).resolve()
