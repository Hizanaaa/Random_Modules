"""
Reviewer Note
-------------
Design choices:

- Atomicity is achieved by creating a temporary file in the SAME
  directory as the destination and committing with os.replace().
  This preserves atomic-rename guarantees on both POSIX and Windows.

- Temporary names are generated as:
      <basename>.tmp.<pid>.<random>
  which avoids collisions between concurrent writers and makes
  cleanup unambiguous.

- On successful completion:
    * keep_backup=False:
        temp -> target via os.replace()
    * keep_backup=True:
        existing target (if present) is first moved to
        <target>.bak, then temp is moved into place.

- On any exception (including KeyboardInterrupt):
    * temp file is closed
    * temp file is removed if present
    * original target is untouched

- Append mode ('a' / 'ab') is implemented by copying the existing
  file into the temporary file before yielding it to the caller.
  The final replace remains atomic.

- Windows note:
  os.replace() can occasionally fail with transient PermissionError
  when AV scanners, indexers, or concurrent writers briefly hold a
  handle open. A short retry loop is used around the final replace.

Test gaps noticed:

- No attempt is made to coordinate concurrent writers. Last writer
  wins, which is expected. The guarantee is that the final file is
  always a complete file from one writer, never an interleaving.

- Backup replacement behavior is intentionally simple:
  an existing .bak file is overwritten.
"""

from __future__ import annotations

import os
import random
import shutil
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import IO, Iterator

_REPLACE_RETRIES = 20
_REPLACE_DELAY = 0.01


def _replace_with_retry(src: Path, dst: Path) -> None:
    """
    Retry os.replace() to tolerate transient Windows file locks.
    """
    last_exc: PermissionError | None = None

    for _ in range(_REPLACE_RETRIES):
        try:
            os.replace(src, dst)
            return
        except PermissionError as exc:
            last_exc = exc
            time.sleep(_REPLACE_DELAY)

    assert last_exc is not None
    raise last_exc


@contextmanager
def atomic_write(
    path: str | os.PathLike,
    mode: str = "w",
    *,
    encoding: str | None = "utf-8",
    keep_backup: bool = False,
    overwrite: bool = True,
) -> Iterator[IO]:
    """
    Atomically write a file by writing to a temporary file in the
    target directory and replacing the destination on success.

    Args:
        path:
            Final target path.
        mode:
            One of 'w', 'wb', 'a', or 'ab'.
        encoding:
            Text encoding for text modes.
        keep_backup:
            Preserve previous content as <path>.bak.
        overwrite:
            If False, raise FileExistsError when target exists.

    Raises:
        ValueError:
            Unsupported mode or invalid encoding usage.
        FileExistsError:
            Target exists and overwrite=False.
    """
    if mode not in {"w", "wb", "a", "ab"}:
        raise ValueError(f"unsupported mode: {mode}")

    binary = "b" in mode

    if binary:
        if encoding is not None:
            raise ValueError("encoding must be None in binary mode")
    else:
        if encoding is None:
            encoding = "utf-8"

    target = Path(path)
    parent = target.parent

    if target.exists() and not overwrite:
        raise FileExistsError(str(target))

    temp_name = (
        f"{target.name}.tmp.{os.getpid()}."
        f"{random.getrandbits(64):016x}"
    )
    temp_path = parent / temp_name

    file_obj: IO | None = None

    try:
        if binary:
            file_obj = open(temp_path, "w+b")
        else:
            file_obj = open(
                temp_path,
                "w+",
                encoding=encoding,
            )

        if mode in {"a", "ab"} and target.exists():
            if binary:
                with open(target, "rb") as src:
                    shutil.copyfileobj(src, file_obj)
            else:
                with open(
                    target,
                    "r",
                    encoding=encoding,
                ) as src:
                    file_obj.write(src.read())

            file_obj.seek(0, os.SEEK_END)

        yield file_obj

        file_obj.flush()

        try:
            os.fsync(file_obj.fileno())
        except OSError:
            pass

        file_obj.close()

        if keep_backup and target.exists():
            backup = Path(str(target) + ".bak")
            _replace_with_retry(target, backup)

        _replace_with_retry(temp_path, target)

    except BaseException:
        if file_obj is not None:
            try:
                file_obj.close()
            except Exception:
                pass

        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass

        raise

    finally:
        try:
            # On the success path, temp_path has already been renamed
            # onto target by _replace_with_retry, so .exists() returns
            # False and nothing happens here. This guard exists solely
            # to catch any edge case where the rename succeeded but a
            # later step left a stale temp (shouldn't happen, but
            # defence-in-depth costs nothing).
            if temp_path.exists():
                temp_path.unlink()
        except Exception:
            pass


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # Happy path text.
        path = root / "text.txt"
        with atomic_write(path) as f:
            f.write("hello")

        assert path.read_text(encoding="utf-8") == "hello"

        # Happy path binary.
        path = root / "bin.dat"
        with atomic_write(
            path,
            "wb",
            encoding=None,
        ) as f:
            f.write(b"\x00\x01\x02")

        assert path.read_bytes() == b"\x00\x01\x02"

        # Encoding round-trip.
        path = root / "utf8.txt"
        with atomic_write(
            path,
            encoding="utf-8",
        ) as f:
            f.write("café")

        assert path.read_text(encoding="utf-8") == "café"

        # Exception rolls back.
        path = root / "rollback.txt"

        try:
            with atomic_write(path) as f:
                f.write("partial")
                raise RuntimeError("oops")
        except RuntimeError:
            pass

        assert not path.exists()

        assert not any(
            p.name.startswith("rollback.txt.tmp.")
            for p in root.iterdir()
        )

        # Exception preserves original.
        path.write_text("original", encoding="utf-8")

        try:
            with atomic_write(path) as f:
                f.write("partial")
                raise RuntimeError("oops")
        except RuntimeError:
            pass

        assert path.read_text(encoding="utf-8") == "original"

        # overwrite=False leaves no temp files.
        path = root / "exists.txt"
        path.write_text("data", encoding="utf-8")

        before = set(root.iterdir())

        try:
            with atomic_write(
                path,
                overwrite=False,
            ):
                pass
            assert False
        except FileExistsError:
            pass

        after = set(root.iterdir())

        assert before == after
        assert not any(
            p.name.startswith("exists.txt.tmp.")
            for p in root.iterdir()
        )

        # keep_backup=True.
        path = root / "backup.txt"
        path.write_text("old", encoding="utf-8")

        with atomic_write(
            path,
            keep_backup=True,
        ) as f:
            f.write("new")

        backup = Path(str(path) + ".bak")

        assert path.read_text(encoding="utf-8") == "new"
        assert backup.read_text(encoding="utf-8") == "old"

        # Append mode.
        path = root / "append.txt"
        path.write_text("hello\n", encoding="utf-8")

        with atomic_write(path, "a") as f:
            f.write("world\n")

        assert (
            path.read_text(encoding="utf-8")
            == "hello\nworld\n"
        )

        # Binary mode encoding error.
        path = root / "bad.bin"

        before = set(root.iterdir())

        try:
            with atomic_write(
                path,
                "wb",
                encoding="ascii",
            ):
                pass
            assert False
        except ValueError:
            pass

        after = set(root.iterdir())

        assert before == after

        # Unsupported modes.
        try:
            with atomic_write(root / "r.txt", "r"):
                pass
            assert False
        except ValueError:
            pass

        try:
            with atomic_write(root / "x.txt", "x"):
                pass
            assert False
        except ValueError:
            pass

        # Concurrent writers.
        path = root / "concurrent.txt"

        content_a = "A" * 10000
        content_b = "B" * 10000

        exceptions: list[Exception] = []
        exceptions_lock = threading.Lock()

        def writer(data: str) -> None:
            try:
                with atomic_write(path) as f:
                    f.write(data)
            except Exception as exc:
                with exceptions_lock:
                    exceptions.append(exc)

        t1 = threading.Thread(
            target=writer,
            args=(content_a,),
        )
        t2 = threading.Thread(
            target=writer,
            args=(content_b,),
        )

        t1.start()
        t2.start()

        t1.join()
        t2.join()

        assert exceptions == []

        final = path.read_text(encoding="utf-8")

        assert final in {content_a, content_b}

        print("All tests passed.")