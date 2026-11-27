"""Output storage: local directory (tests, dry runs) or Cloudflare R2 (S3 API)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Protocol

PNG_CACHE = "public, max-age=86400, immutable"  # names contain the time → never change
INDEX_CACHE = "public, max-age=30, must-revalidate"


class Store(Protocol):
    def put(self, key: str, data: bytes, content_type: str, cache_control: str) -> None: ...
    def keys(self, prefix: str) -> set[str]: ...
    def delete(self, keys: list[str]) -> None: ...


class LocalStore:
    def __init__(self, root: Path):
        self.root = Path(root)

    def put(self, key: str, data: bytes, content_type: str, cache_control: str) -> None:
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_bytes(data)
        tmp.replace(path)

    def keys(self, prefix: str) -> set[str]:
        base = self.root / prefix
        if not base.exists():
            return set()
        return {p.relative_to(self.root).as_posix() for p in base.rglob("*") if p.is_file() and not p.name.endswith(".tmp")}

    def delete(self, keys: list[str]) -> None:
        for k in keys:
            (self.root / k).unlink(missing_ok=True)
        # remove empty folders below the root
        for d in sorted((p for p in self.root.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
            if not any(d.iterdir()):
                d.rmdir()


class R2Store:
    """Cloudflare R2 via boto3. Credentials from the environment (see .env.example)."""

    def __init__(self, bucket: str | None = None):
        import boto3

        account = os.environ["R2_ACCOUNT_ID"]
        self.bucket = bucket or os.environ["R2_BUCKET"]
        self.s3 = boto3.client(
            "s3",
            endpoint_url=f"https://{account}.r2.cloudflarestorage.com",
            aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
            region_name="auto",
        )

    def put(self, key: str, data: bytes, content_type: str, cache_control: str) -> None:
        self.s3.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type, CacheControl=cache_control)

    def keys(self, prefix: str) -> set[str]:
        out: set[str] = set()
        for page in self.s3.get_paginator("list_objects_v2").paginate(Bucket=self.bucket, Prefix=prefix):
            out.update(o["Key"] for o in page.get("Contents", []))
        return out

    def delete(self, keys: list[str]) -> None:
        for i in range(0, len(keys), 1000):
            chunk = keys[i:i + 1000]
            self.s3.delete_objects(Bucket=self.bucket, Delete={"Objects": [{"Key": k} for k in chunk], "Quiet": True})
