"""Replace portable metadata only after staging it, retaining the previous version."""
import os
import tempfile
from pathlib import Path


def atomic_write(path: Path, content: bytes, *, backup: bool = True) -> None:
    if path.exists() and path.read_bytes() == content:
        return
    descriptor, temporary = tempfile.mkstemp(prefix=f'.{path.name}.', suffix='.tmp', dir=path.parent)
    staged = Path(temporary)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if backup and path.exists():
            atomic_write(path.with_name(path.name + '.bak'), path.read_bytes(), backup=False)
        os.replace(staged, path)
    finally:
        staged.unlink(missing_ok=True)


def atomic_copy(source: Path, target: Path) -> None:
    if source.resolve() != target.resolve():
        atomic_write(target, source.read_bytes())
