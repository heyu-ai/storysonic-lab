"""Configured RSS catalogues; network and feed data are untrusted inputs."""

from dataclasses import dataclass
from datetime import timezone
from email.utils import parsedate_to_datetime
import hashlib
from pathlib import Path
import re
import tomllib
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import xml.etree.ElementTree as ET


MAX_FEED_BYTES = 20 * 1024 * 1024
AUDIO_FORMATS = {'audio/mpeg': ('mp3', 'audio/mpeg'), 'audio/mp3': ('mp3', 'audio/mpeg'),
                 'audio/mp4': ('m4a', 'audio/mp4'), 'audio/m4a': ('m4a', 'audio/mp4'),
                 'audio/x-m4a': ('m4a', 'audio/mp4')}


USER_AGENT = 'StorySonic-Lab/0.2.0 (podcast research)'


def validate_url(url):
    parsed = urlsplit(url)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('來源必須是無帳密的 HTTP(S) URL')
    if any(ord(c) < 32 for c in url):
        raise ValueError('URL 含控制字元')
    return url


class SafeRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def open_http(url):
    validate_url(url)
    return build_opener(SafeRedirect()).open(
        Request(url, headers={'User-Agent': USER_AGENT, 'Accept-Encoding': 'identity'}), timeout=30
    )


def validate_id(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', value) or len(value) > 80:
        raise ValueError('ID 必須為 1–80 字元的小寫英文、數字與連字號')
    return value


@dataclass(frozen=True)
class Show:
    id: str
    name: str
    podcaster_id: str
    podcaster_name: str
    feed_url: str

    def __post_init__(self):
        validate_id(self.id)
        validate_id(self.podcaster_id)
        validate_url(self.feed_url)
        if not self.name.strip() or not self.podcaster_name.strip():
            raise ValueError('節目與 podcaster 顯示名稱不可空白')


def load_config(path):
    with Path(path).open('rb') as file:
        config = tomllib.load(file)
    shows = {}
    publishers = {}
    for raw in config.get('shows', []):
        show = Show(**raw)
        if show.id in shows:
            raise ValueError(f'重複節目 ID: {show.id}')
        if show.podcaster_id in publishers and publishers[show.podcaster_id] != show.podcaster_name:
            raise ValueError(f'同一 podcaster ID 的顯示名稱不一致: {show.podcaster_id}')
        publishers[show.podcaster_id] = show.podcaster_name
        shows[show.id] = show
    if not shows:
        raise ValueError('設定檔沒有 shows')
    return config.get('drive', {}).get('folder', ''), shows


def date_key(value):
    try:
        date = parsedate_to_datetime(value)
        return date.replace(tzinfo=date.tzinfo or timezone.utc).timestamp()
    except (ValueError, TypeError, OverflowError):
        return float('-inf')


def parse_feed(data, show):
    if len(data) > MAX_FEED_BYTES:
        raise ValueError('RSS 超過 20 MiB 限制')
    # Also catch declarations in UTF-16/32 inputs before ElementTree expansion.
    declarations = data.replace(b'\x00', b'').upper()
    if b'<!DOCTYPE' in declarations or b'<!ENTITY' in declarations:
        raise ValueError('RSS 不接受 DTD 或 entity 宣告')
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise ValueError(f'RSS XML 無效: {exc}') from exc
    channel = root.find('channel')
    if root.tag != 'rss' or channel is None:
        raise ValueError('來源不是 RSS 2.0 channel')
    seen, episodes = set(), []
    for item in channel.findall('item'):
        enclosure = item.find('enclosure')
        if enclosure is None:
            continue
        url = enclosure.get('url', '').strip()
        media_type = enclosure.get('type', '').lower().split(';')[0]
        format_ = AUDIO_FORMATS.get(media_type)
        if not media_type:
            suffix = Path(urlsplit(url).path).suffix.lower()
            format_ = {'.mp3': ('mp3', 'audio/mpeg'), '.m4a': ('m4a', 'audio/mp4')}.get(suffix)
        if not format_:
            continue
        extension, canonical_type = format_
        validate_url(url)
        guid = (item.findtext('guid') or url).strip() or url
        if guid in seen:
            continue
        seen.add(guid)
        try:
            declared = max(0, int(enclosure.get('length', '0')))
        except ValueError:
            declared = 0
        episodes.append({
            'episode_key': hashlib.sha256(f'{show.id}\0{guid}'.encode()).hexdigest()[:24],
            'show_id': show.id, 'show_name': show.name,
            'podcaster_id': show.podcaster_id, 'podcaster_name': show.podcaster_name,
            'feed_url': show.feed_url, 'guid': guid,
            'title': (item.findtext('title') or '').strip() or guid,
            'published': (item.findtext('pubDate') or '').strip(),
            'enclosure_url': url, 'declared_bytes': declared,
            'extension': extension, 'media_type': canonical_type,
        })
    return sorted(episodes, key=lambda e: date_key(e['published']), reverse=True)


def fetch_episodes(show, opener=None):
    with (opener or open_http)(show.feed_url) as response:
        data = response.read(MAX_FEED_BYTES + 1)
    return parse_feed(data, show)


def select_episodes(episodes, match='', limit=3):
    if limit is not None and (type(limit) is not int or limit <= 0):
        raise ValueError('limit 必須為正整數；全部請使用 --all')
    selected = [e for e in episodes if match.casefold() in e['title'].casefold()]
    selected.sort(key=lambda e: date_key(e['published']), reverse=True)
    return selected if limit is None else selected[:limit]
