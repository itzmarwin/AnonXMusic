import asyncio
import re
import time
from typing import Any

import aiohttp

from anony.helpers import utils


_MUSIC_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
_MUSIC_PARAMS_VIDEOS = "EgWKAQIQAWoKEAoQAxAEEAkQBQ=="
_MUSIC_PARAMS_SONGS = "EgWKAQIIAWoKEAoQAxAEEAkQBQ=="
_MUSIC_CLIENT_TTL = 6 * 3600
_MUSIC_DURATION = re.compile(r"^\d{1,2}:\d{2}(?::\d{2})?$")
_MUSIC_TYPE_LABELS = {"video", "song", "album", "single", "ep", "playlist"}
_music_client_cache = {"key": "", "version": "", "expires": 0.0}


def _music_renderers(node: Any):
    if isinstance(node, dict):
        renderer = node.get("musicResponsiveListItemRenderer")
        if isinstance(renderer, dict):
            yield renderer
        for value in node.values():
            yield from _music_renderers(value)
    elif isinstance(node, list):
        for value in node:
            yield from _music_renderers(value)


def _music_runs(column: Any) -> list[str]:
    if not isinstance(column, dict):
        return []
    renderer = column.get("musicResponsiveListItemFlexColumnRenderer")
    text = renderer.get("text") if isinstance(renderer, dict) else None
    runs = text.get("runs") if isinstance(text, dict) else None
    return [
        str(run.get("text") or "")
        for run in runs or []
        if isinstance(run, dict)
    ]


def _music_watch_id(node: Any) -> str:
    if isinstance(node, dict):
        endpoint = node.get("watchEndpoint")
        if isinstance(endpoint, dict):
            video_id = str(endpoint.get("videoId") or "")
            if len(video_id) == 11 and all(
                ch.isalnum() or ch in "_-" for ch in video_id
            ):
                return video_id
        for value in node.values():
            found = _music_watch_id(value)
            if found:
                return found
    elif isinstance(node, list):
        for value in node:
            found = _music_watch_id(value)
            if found:
                return found
    return ""


def _music_thumbnail(renderer: dict) -> str:
    thumbnail = renderer.get("thumbnail") or {}
    music = thumbnail.get("musicThumbnailRenderer")
    inner = music.get("thumbnail") if isinstance(music, dict) else None
    thumbnails = inner.get("thumbnails") if isinstance(inner, dict) else None
    if not thumbnails or not isinstance(thumbnails[-1], dict):
        return ""
    url = str(thumbnails[-1].get("url") or "")
    if not url:
        return ""
    return re.sub(r"=w\d+-h\d+", "=w544-h544", url)


def _music_entry(renderer: dict) -> dict | None:
    columns = renderer.get("flexColumns") or []
    title = ""
    if columns:
        title = " ".join(part for part in _music_runs(columns[0]) if part).strip()
    duration = ""
    channel = ""
    for column in columns[1:]:
        for raw in _music_runs(column):
            value = raw.strip()
            if not value or value == "•":
                continue
            if _MUSIC_DURATION.match(value):
                duration = value
                continue
            if value.lower() in _MUSIC_TYPE_LABELS:
                continue
            if not channel:
                channel = value
    video_id = _music_watch_id(renderer.get("overlay") or {})
    if not video_id and columns:
        video_id = _music_watch_id(columns[0])
    if not video_id:
        return None
    duration = duration or "00:00"
    return {
        "id": video_id,
        "title": title or video_id,
        "duration": duration,
        "duration_sec": utils.to_seconds(duration),
        "thumbnail": _music_thumbnail(renderer),
        "channel_name": channel,
        "url": f"https://www.youtube.com/watch?v={video_id}",
    }


def _music_tracks(data: Any, limit: int) -> list[dict]:
    tracks = []
    seen = set()
    for renderer in _music_renderers(data):
        entry = _music_entry(renderer)
        if entry is None or entry["id"] in seen:
            continue
        seen.add(entry["id"])
        tracks.append(entry)
        if len(tracks) >= limit:
            break
    return tracks


async def _music_client(session: aiohttp.ClientSession) -> tuple[str, str]:
    now = time.monotonic()
    key = str(_music_client_cache.get("key") or "")
    version = str(_music_client_cache.get("version") or "")
    if key and version and float(_music_client_cache.get("expires") or 0) > now:
        return key, version
    async with session.get("https://music.youtube.com/") as resp:
        resp.raise_for_status()
        html = await resp.text()
    key_match = re.search(r'"INNERTUBE_API_KEY":"([^"]+)"', html)
    version_match = re.search(r'"INNERTUBE_CLIENT_VERSION":"([^"]+)"', html)
    if key_match is None or version_match is None:
        raise RuntimeError("youtube music client config missing")
    key = key_match.group(1)
    version = version_match.group(1)
    _music_client_cache.update(
        key=key,
        version=version,
        expires=now + _MUSIC_CLIENT_TTL,
    )
    return key, version


async def _music_search_page(
    session: aiohttp.ClientSession, query: str, params: str = ""
) -> list[dict]:
    key, version = await _music_client(session)
    body = {
        "context": {
            "client": {
                "clientName": "WEB_REMIX",
                "clientVersion": version,
                "hl": "en",
                "gl": "US",
            }
        },
        "query": query,
    }
    if params:
        body["params"] = params
    headers = {
        "Origin": "https://music.youtube.com",
        "Referer": "https://music.youtube.com/",
    }
    for attempt in range(2):
        async with session.post(
            "https://music.youtube.com/youtubei/v1/search",
            params={"key": key, "prettyPrint": "false"},
            json=body,
            headers=headers,
        ) as resp:
            if resp.status in (400, 403) and attempt == 0:
                _music_client_cache.update(key="", version="", expires=0.0)
                key, version = await _music_client(session)
                body["context"]["client"]["clientVersion"] = version
                continue
            resp.raise_for_status()
            data = await resp.json(content_type=None)
        return _music_tracks(data, 50)
    return []


async def search_music(query: str, limit: int = 1) -> list[dict]:
    timeout = aiohttp.ClientTimeout(total=25)
    headers = {
        "User-Agent": _MUSIC_UA,
        "Accept-Language": "en-US,en;q=0.9",
    }
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        await _music_client(session)
        primary, videos, songs = await asyncio.gather(
            _music_search_page(session, query),
            _music_search_page(session, query, _MUSIC_PARAMS_VIDEOS),
            _music_search_page(session, query, _MUSIC_PARAMS_SONGS),
            return_exceptions=True,
        )
        if isinstance(primary, BaseException):
            primary = []
        if isinstance(videos, BaseException):
            videos = []
        if isinstance(songs, BaseException):
            songs = []
        if primary:
            durations = {
                track["id"]: track["duration"]
                for track in list(videos) + list(songs)
                if track["duration"] != "00:00"
            }
            for track in primary:
                if track["duration"] == "00:00" and track["id"] in durations:
                    track["duration"] = durations[track["id"]]
                    track["duration_sec"] = utils.to_seconds(track["duration"])
            return primary[:limit]
        if videos:
            return videos[:limit]
        return songs[:limit]
