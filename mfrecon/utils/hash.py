"""Hashing utility to calculate file integrity checksums."""

import hashlib
from pathlib import Path

from mfrecon.core.exceptions import FileAccessError


def calculate_sha256(file_path: Path) -> str:
    """
    Computes the SHA-256 checksum of the target file.

    Args:
        file_path: Path to the target file.

    Returns:
        str: Hexadecimal string representing the SHA-256 hash.

    Raises:
        FileAccessError: If the file cannot be found or read.
    """
    if not file_path.exists() or not file_path.is_file():
        raise FileAccessError(f"Target file for hashing does not exist or is not a file: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with file_path.open("rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except OSError as e:
        raise FileAccessError(f"Failed to read file for hashing: {e}") from e
