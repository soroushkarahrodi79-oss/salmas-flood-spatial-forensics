"""Small, auditable HTTP acquisition primitives."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import requests


USER_AGENT = "salmas-flood-spatial-forensics/0.2 (+https://github.com/soroushkarahrodi79-oss/salmas-flood-spatial-forensics)"


@dataclass(frozen=True)
class AcquisitionRecord:
    asset_id: str
    provider: str
    dataset: str
    url: str
    path: str
    retrieved_utc: str
    size_bytes: int
    sha256: str
    role: str
    license_or_terms: str


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(chunk_size), b""):
            digest.update(block)
    return digest.hexdigest()


def _download(url: str, destination: Path, timeout: int = 60) -> None:
    """Download with a resumable .part file and atomic final rename."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + ".part")
    offset = partial.stat().st_size if partial.exists() else 0
    headers = {"User-Agent": USER_AGENT}
    if offset:
        headers["Range"] = f"bytes={offset}-"
    with requests.get(url, headers=headers, stream=True, timeout=timeout) as response:
        if offset and response.status_code == 200:
            partial.unlink()
            offset = 0
        elif offset and response.status_code != 206:
            response.raise_for_status()
        else:
            response.raise_for_status()
        mode = "ab" if offset else "wb"
        with partial.open(mode) as handle:
            for block in response.iter_content(chunk_size=1024 * 1024):
                if block:
                    handle.write(block)
            handle.flush()
            os.fsync(handle.fileno())
    partial.replace(destination)


def acquire(asset: dict[str, str], root: Path, force: bool = False) -> AcquisitionRecord:
    destination = root / asset["destination"]
    if force or not destination.exists():
        _download(asset["url"], destination)
    if destination.stat().st_size == 0:
        raise ValueError(f"Empty acquisition: {asset['asset_id']}")
    return AcquisitionRecord(
        asset_id=asset["asset_id"],
        provider=asset["provider"],
        dataset=asset["dataset"],
        url=asset["url"],
        path=asset["destination"],
        retrieved_utc=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        size_bytes=destination.stat().st_size,
        sha256=sha256_file(destination),
        role=asset["role"],
        license_or_terms=asset["license_or_terms"],
    )


def write_manifest(records: Iterable[AcquisitionRecord], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted((asdict(record) for record in records), key=lambda row: row["asset_id"])
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
