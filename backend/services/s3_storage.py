from __future__ import annotations

from dataclasses import dataclass
import mimetypes
from pathlib import PurePosixPath
import re
from urllib.parse import quote
from uuid import uuid4

import boto3
from botocore.client import BaseClient
from botocore.config import Config
from botocore.exceptions import ClientError
from PIL import Image, UnidentifiedImageError

from backend.core.config import settings
from backend.core.logger_config import logger


class S3ConfigError(RuntimeError):
    pass


class S3InvalidImageError(ValueError):
    pass


@dataclass
class S3ObjectRef:
    key: str
    url: str


def _require(value: str | None, name: str) -> str:
    if value and value.strip():
        return value.strip()
    raise S3ConfigError(f"{name} is not configured")


def _safe_name(filename: str) -> str:
    base = (filename or "image").strip().replace("\\", "_").replace("/", "_")
    # Telegram is picky with remote media URLs; keep object names ASCII-only.
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", base)
    base = re.sub(r"_+", "_", base).strip("._-")
    return (base[:80] or "image")


def _pick_extension(filename: str, content_type: str | None) -> str:
    safe_name = _safe_name(filename)
    m = re.search(r"\.([A-Za-z0-9]{1,8})$", safe_name)
    if m:
        return "." + m.group(1).lower()
    guessed = mimetypes.guess_extension((content_type or "").strip() or "") or ""
    if guessed and re.fullmatch(r"\.[A-Za-z0-9]{1,8}", guessed):
        return guessed.lower()
    return ".jpg"


def _detect_image_meta(stream) -> tuple[str, str] | None:
    """
    Detect real image format from file bytes.
    Returns: (extension, content_type)
    """
    format_map: dict[str, tuple[str, str]] = {
        "JPEG": (".jpg", "image/jpeg"),
        "PNG": (".png", "image/png"),
        "WEBP": (".webp", "image/webp"),
        "GIF": (".gif", "image/gif"),
        "BMP": (".bmp", "image/bmp"),
    }
    try:
        stream.seek(0)
        with Image.open(stream) as img:
            fmt = (img.format or "").upper()
        return format_map.get(fmt)
    except (UnidentifiedImageError, OSError, ValueError):
        return None
    finally:
        stream.seek(0)


class S3StorageService:
    def __init__(self) -> None:
        self.bucket = _require(settings.S3_BUCKET_NAME, "S3_BUCKET_NAME")
        self.public_base = (settings.S3_PUBLIC_BASE_URL or "").rstrip("/")
        # Keep flat keys per shop, but respect configured public prefix/policy.
        self.media_prefix = (settings.S3_MEDIA_PREFIX or "shops").strip().strip("/")
        self.legacy_media_prefix = "shops" if self.media_prefix != "shops" else ""
        self.client = self._build_client()

    def _build_client(self) -> BaseClient:
        access_key = _require(settings.S3_ACCESS_KEY_ID, "S3_ACCESS_KEY_ID")
        secret_key = _require(settings.S3_SECRET_ACCESS_KEY, "S3_SECRET_ACCESS_KEY")

        kwargs: dict = {
            "service_name": "s3",
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "config": Config(s3={"addressing_style": "path" if settings.S3_USE_PATH_STYLE else "auto"}),
        }
        if settings.S3_ENDPOINT_URL:
            kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL
        if settings.S3_REGION:
            kwargs["region_name"] = settings.S3_REGION
        return boto3.client(**kwargs)

    def _build_public_url(self, key: str) -> str:
        if self.public_base:
            return f"{self.public_base}/{quote(key)}"

        if settings.S3_ENDPOINT_URL:
            endpoint = settings.S3_ENDPOINT_URL.rstrip("/")
            return f"{endpoint}/{self.bucket}/{quote(key)}"

        return f"https://{self.bucket}.s3.amazonaws.com/{quote(key)}"

    def upload_image(self, *, shop_id: int, entity: str, filename: str, content_type: str | None, stream) -> S3ObjectRef:
        _ = entity  # kept for API compatibility; keys are unified across entities.
        detected = _detect_image_meta(stream)
        if detected:
            ext, resolved_content_type = detected
        else:
            provided_type = (content_type or "").strip()
            if provided_type and not provided_type.startswith("image/"):
                raise S3InvalidImageError("Uploaded file is not a valid image")
            ext = _pick_extension(filename, content_type)
            resolved_content_type = provided_type
            if not resolved_content_type.startswith("image/"):
                guessed_by_ext = mimetypes.guess_type(f"x{ext}")[0]
                resolved_content_type = guessed_by_ext or "image/jpeg"
        short_id = uuid4().hex[:16]
        # Keep one flat folder per shop: shops/<shop_id>/<file>
        key = str(PurePosixPath(self.media_prefix) / str(shop_id) / f"{short_id}{ext}")
        extra = {"ContentType": resolved_content_type}

        # Telegram fetches media by public URL, so prefer public-read ACL where supported.
        try:
            self.client.upload_fileobj(stream, self.bucket, key, ExtraArgs={**extra, "ACL": "public-read"})
        except ClientError as e:
            code = str(e.response.get("Error", {}).get("Code", ""))
            if code not in ("AccessControlListNotSupported", "InvalidRequest"):
                raise
            logger.warning(f"[S3] ACL not supported for bucket='{self.bucket}', retry upload without ACL")
            stream.seek(0)
            self.client.upload_fileobj(stream, self.bucket, key, ExtraArgs=extra)
        ref = S3ObjectRef(key=key, url=self._build_public_url(key))
        logger.info(f"[S3] uploaded image key='{ref.key}' content_type='{resolved_content_type}' url='{ref.url}'")
        return ref

    def list_images(self, *, shop_id: int, entity: str, limit: int = 200) -> list[S3ObjectRef]:
        _ = entity  # API compatibility: media library is shared for all entities.
        prefixes = [
            f"{self.media_prefix}/{shop_id}/",         # current flat format
            f"{self.media_prefix}/{shop_id}/i/",       # previous code-based format
            f"{self.media_prefix}/{shop_id}/c/",
            f"m/{shop_id}/i/",                         # previous short format
            f"m/{shop_id}/c/",
            f"shops/{shop_id}/items/",                 # legacy entity folders
            f"shops/{shop_id}/categories/",
        ]
        if self.legacy_media_prefix:
            prefixes.extend(
                [
                    f"{self.legacy_media_prefix}/{shop_id}/",
                    f"{self.legacy_media_prefix}/{shop_id}/i/",
                    f"{self.legacy_media_prefix}/{shop_id}/c/",
                ]
            )
        out: list[S3ObjectRef] = []
        paginator = self.client.get_paginator("list_objects_v2")

        seen: set[str] = set()
        for prefix in prefixes:
            for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
                for obj in page.get("Contents", []):
                    key = obj.get("Key")
                    if not key or key in seen:
                        continue
                    seen.add(key)
                    out.append(S3ObjectRef(key=key, url=self._build_public_url(key)))
                    if len(out) >= limit:
                        return out
        return out
