from __future__ import annotations

from contextlib import suppress
from collections import OrderedDict
from urllib.parse import urlparse
import mimetypes

import aiohttp

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import BufferedInputFile, InputMediaPhoto, Message

_MEDIA_FILE_ID_CACHE: "OrderedDict[str, str]" = OrderedDict()
_MEDIA_FILE_ID_CACHE_MAX = 1000
_HTTP_SESSION: aiohttp.ClientSession | None = None


def _is_bad_media_error(error: TelegramBadRequest) -> bool:
    text = str(error).lower()
    return (
        "wrong type of the web page content" in text
        or "failed to get http url content" in text
        or "wrong file identifier/http url specified" in text
    )


def _is_not_modified_error(error: TelegramBadRequest) -> bool:
    return "message is not modified" in str(error).lower()


def _cache_get(url: str) -> str | None:
    key = url.strip()
    if not key:
        return None
    value = _MEDIA_FILE_ID_CACHE.get(key)
    if value:
        _MEDIA_FILE_ID_CACHE.move_to_end(key)
    return value


def _cache_put(url: str, file_id: str | None) -> None:
    key = url.strip()
    value = (file_id or "").strip()
    if not key or not value:
        return
    _MEDIA_FILE_ID_CACHE[key] = value
    _MEDIA_FILE_ID_CACHE.move_to_end(key)
    while len(_MEDIA_FILE_ID_CACHE) > _MEDIA_FILE_ID_CACHE_MAX:
        _MEDIA_FILE_ID_CACHE.popitem(last=False)


def _cache_drop(url: str) -> None:
    _MEDIA_FILE_ID_CACHE.pop((url or "").strip(), None)


def _extract_photo_file_id(result: Message | bool | None) -> str | None:
    if not isinstance(result, Message):
        return None
    photos = getattr(result, "photo", None) or []
    if not photos:
        return None
    return (photos[-1].file_id or "").strip() or None


async def _get_http_session() -> aiohttp.ClientSession:
    global _HTTP_SESSION
    if _HTTP_SESSION is None or _HTTP_SESSION.closed:
        timeout = aiohttp.ClientTimeout(total=12)
        connector = aiohttp.TCPConnector(limit=64, ttl_dns_cache=300)
        _HTTP_SESSION = aiohttp.ClientSession(timeout=timeout, connector=connector)
    return _HTTP_SESSION


def _guess_ext_from_url_or_type(url: str, content_type: str | None) -> str:
    mime = (content_type or "").split(";")[0].strip().lower()
    ext = mimetypes.guess_extension(mime) or ""
    if ext in (".jpe",):
        ext = ".jpg"
    if ext:
        return ext

    path = urlparse(url).path
    url_ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    if url_ext in {"jpg", "jpeg", "png", "webp", "gif", "bmp"}:
        return ".jpg" if url_ext == "jpeg" else f".{url_ext}"
    return ".jpg"


async def _download_remote_image_as_input_file(url: str) -> BufferedInputFile | None:
    try:
        session = await _get_http_session()
        async with session.get(url, allow_redirects=True) as resp:
            if resp.status != 200:
                return None
            payload = await resp.read()
            if not payload or len(payload) > 15 * 1024 * 1024:
                return None
            ext = _guess_ext_from_url_or_type(url, resp.headers.get("Content-Type"))
            return BufferedInputFile(payload, filename=f"media{ext}")
    except Exception:
        return None


async def _delete_and_send_text(
    *,
    message: Message,
    text: str,
    reply_markup=None,
    parse_mode: str | None = "HTML",
) -> None:
    with suppress(Exception):
        await message.delete()
    await message.answer(text=text, parse_mode=parse_mode, reply_markup=reply_markup)


async def safe_edit_photo_or_text(
    *,
    message: Message,
    image: str | None,
    text: str,
    reply_markup=None,
    parse_mode: str | None = "HTML",
) -> None:
    media_url = (image or "").strip()
    if media_url:
        cached_file_id = _cache_get(media_url)
        if cached_file_id:
            try:
                result = await message.edit_media(
                    media=InputMediaPhoto(media=cached_file_id, caption=text, parse_mode=parse_mode),
                    reply_markup=reply_markup,
                )
                _cache_put(media_url, _extract_photo_file_id(result) or cached_file_id)
                return
            except TelegramBadRequest as cached_error:
                if _is_not_modified_error(cached_error):
                    return
                if _is_bad_media_error(cached_error):
                    _cache_drop(media_url)
                else:
                    raise
        try:
            result = await message.edit_media(
                media=InputMediaPhoto(media=media_url, caption=text, parse_mode=parse_mode),
                reply_markup=reply_markup,
            )
            _cache_put(media_url, _extract_photo_file_id(result))
            return
        except TelegramBadRequest as error:
            if _is_not_modified_error(error):
                return
            if not _is_bad_media_error(error):
                raise

            # Fallback: fetch remote image ourselves and upload as binary file.
            uploaded = await _download_remote_image_as_input_file(media_url)
            if uploaded is not None:
                try:
                    result = await message.edit_media(
                        media=InputMediaPhoto(media=uploaded, caption=text, parse_mode=parse_mode),
                        reply_markup=reply_markup,
                    )
                    _cache_put(media_url, _extract_photo_file_id(result))
                    return
                except TelegramBadRequest as upload_error:
                    if _is_not_modified_error(upload_error):
                        return

            # Wanted to show an image, but Telegram rejected it.
            # If current message is text -> switch to text safely.
            if getattr(message, "text", None) is not None:
                try:
                    await message.edit_text(text=text, parse_mode=parse_mode, reply_markup=reply_markup)
                    return
                except TelegramBadRequest as text_error:
                    if _is_not_modified_error(text_error):
                        return
            await _delete_and_send_text(
                message=message,
                text=text,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
            )
            return

    # No target image: keep as text; if current message is media, recreate as text.
    if getattr(message, "text", None) is not None:
        try:
            await message.edit_text(text=text, parse_mode=parse_mode, reply_markup=reply_markup)
            return
        except TelegramBadRequest as error:
            if _is_not_modified_error(error):
                return

    await _delete_and_send_text(
        message=message,
        text=text,
        parse_mode=parse_mode,
        reply_markup=reply_markup,
    )


async def safe_answer_photo_or_text(
    *,
    message: Message,
    image: str | None,
    text: str,
    reply_markup=None,
    parse_mode: str | None = "HTML",
) -> None:
    media_url = (image or "").strip()
    if media_url:
        cached_file_id = _cache_get(media_url)
        if cached_file_id:
            try:
                result = await message.answer_photo(
                    photo=cached_file_id,
                    caption=text,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup,
                )
                _cache_put(media_url, _extract_photo_file_id(result) or cached_file_id)
                return
            except TelegramBadRequest as cached_error:
                if _is_bad_media_error(cached_error):
                    _cache_drop(media_url)
                else:
                    raise
        try:
            result = await message.answer_photo(
                photo=media_url,
                caption=text,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
            )
            _cache_put(media_url, _extract_photo_file_id(result))
            return
        except TelegramBadRequest as error:
            if not _is_bad_media_error(error):
                raise
            uploaded = await _download_remote_image_as_input_file(media_url)
            if uploaded is not None:
                try:
                    result = await message.answer_photo(
                        photo=uploaded,
                        caption=text,
                        parse_mode=parse_mode,
                        reply_markup=reply_markup,
                    )
                    _cache_put(media_url, _extract_photo_file_id(result))
                    return
                except TelegramBadRequest:
                    pass

    await message.answer(text=text, parse_mode=parse_mode, reply_markup=reply_markup)
