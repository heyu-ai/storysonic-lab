"""Atomic local downloads and versioned, verifiable episode manifests."""

from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
from http.client import HTTPException
import json
import os
from pathlib import Path
import re
import tempfile
import time

from .catalog import AUDIO_FORMATS, open_http, validate_id, validate_url


MAX_AUDIO_BYTES = 256 * 1024 * 1024


def now():
    return datetime.now(timezone.utc).isoformat()


def safe_path(root, *parts):
    root = Path(root).absolute()
    path = root
    for part in parts:
        if not isinstance(part, str) or not part or Path(part).name != part or part in ('.', '..') or '\\' in part:
            raise ValueError('內容路徑不可越界')
        path = path / part
        if path.is_symlink():
            raise ValueError(f'不接受 symlink: {path.name}')
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('內容路徑不可越界')
    return path


@contextmanager
def content_lock(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    lock = safe_path(root, '.storysonic.lock')
    with lock.open('a') as file:
        try:
            fcntl.flock(file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError('另一個 StorySonic 程序正在寫入此 content 目錄') from exc
        try:
            yield
        finally:
            fcntl.flock(file.fileno(), fcntl.LOCK_UN)


def atomic_json(path, data):
    path = Path(path)
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, prefix='.manifest-', suffix='.part', delete=False) as file:
        temporary = Path(file.name)
        try:
            json.dump(data, file, ensure_ascii=False, indent=2, allow_nan=False)
            file.write('\n')
            file.flush()
            os.fsync(file.fileno())
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def file_hashes(path):
    sha, md5, size = hashlib.sha256(), hashlib.md5(), 0
    with Path(path).open('rb') as file:
        while block := file.read(1024 * 1024):
            sha.update(block)
            md5.update(block)
            size += len(block)
    return {'sha256': sha.hexdigest(), 'md5': md5.hexdigest(), 'bytes': size}


def read_manifest(path, root, show=None):
    path = Path(path).absolute()
    try:
        relative = path.relative_to(Path(root).absolute())
        safe_path(root, *relative.parts)
        data = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(data, dict) or data.get('schema_version') != 1:
            raise ValueError('不支援的 manifest schema')
        for key in ('episode_key', 'show_id', 'show_name', 'podcaster_id', 'podcaster_name', 'feed_url', 'guid', 'title', 'enclosure_url', 'downloaded_at', 'local_file'):
            if not isinstance(data.get(key), str) or not data[key]:
                raise ValueError(f'manifest 缺少 {key}')
        if not isinstance(data.get('published'), str) or not isinstance(data.get('uploads'), dict):
            raise ValueError('manifest 的 published 或 uploads 無效')
        validate_id(data['show_id'])
        validate_id(data['podcaster_id'])
        validate_url(data['feed_url'])
        validate_url(data['enclosure_url'])
        expected_key = hashlib.sha256(f"{data['show_id']}\0{data['guid']}".encode()).hexdigest()[:24]
        if data['episode_key'] != expected_key:
            raise ValueError('manifest episode key 不符合來源')
        expected = Path(data['podcaster_id']) / data['show_id'] / (expected_key + '.json')
        extension = data.get('extension', 'mp3')
        if extension not in ('mp3', 'm4a') or data.get('media_type', 'audio/mpeg') != {'mp3': 'audio/mpeg', 'm4a': 'audio/mp4'}[extension]:
            raise ValueError('manifest 媒體格式無效')
        if relative != expected or data['local_file'] != expected_key + '.' + extension:
            raise ValueError('manifest 內容路徑不符合 episode identity')
        if show and (data['show_id'] != show.id or data['podcaster_id'] != show.podcaster_id):
            raise ValueError('manifest 不屬於選定節目')
        for key, size in [('sha256', 64), ('md5', 32)]:
            if not isinstance(data.get(key), str) or not re.fullmatch('[0-9a-f]{' + str(size) + '}', data[key]):
                raise ValueError(f'manifest {key} 無效')
        if type(data.get('bytes')) is not int or data['bytes'] <= 0:
            raise ValueError('manifest bytes 必須是正整數')
        return data
    except (OSError, json.JSONDecodeError, TypeError) as exc:
        raise ValueError(f'無法讀取 manifest {path.name}: {exc}') from exc


def verified_file(manifest, data, root):
    file = safe_path(root, data['podcaster_id'], data['show_id'], data['local_file'])
    if not file.is_file():
        raise ValueError(f'音檔不存在: {file.name}')
    actual = file_hashes(file)
    if any(actual[key] != data[key] for key in ('bytes', 'sha256', 'md5')):
        raise ValueError(f'音檔大小或雜湊不符: {file.name}；請重跑 download')
    return file


def looks_like_mp3(prefix):
    return prefix.startswith(b'ID3') or (len(prefix) >= 2 and prefix[0] == 0xFF and prefix[1] & 0xE0 == 0xE0)


def download_episode(episode, root, *, opener=None, max_bytes=MAX_AUDIO_BYTES, attempts=3, retry_delay=1):
    if type(max_bytes) is not int or max_bytes <= 0 or type(attempts) is not int or not 1 <= attempts <= 3:
        raise ValueError('max_bytes 必須為正整數，attempts 必須介於 1–3')
    for key in ('podcaster_id', 'show_id'):
        validate_id(episode[key])
    if not re.fullmatch(r'[0-9a-f]{24}', episode['episode_key']):
        raise ValueError('episode key 無效')
    directory = safe_path(root, episode['podcaster_id'], episode['show_id'])
    directory.mkdir(parents=True, exist_ok=True)
    key = episode['episode_key']
    extension = episode.get('extension', 'mp3')
    if extension not in ('mp3', 'm4a'):
        raise ValueError('不支援的音訊格式')
    destination = safe_path(root, episode['podcaster_id'], episode['show_id'], key + '.' + extension)
    manifest = safe_path(root, episode['podcaster_id'], episode['show_id'], key + '.json')
    if manifest.exists():
        existing = read_manifest(manifest, root)
        try:
            verified_file(manifest, existing, root)
            return manifest, 'skipped'
        except ValueError:
            pass  # A missing/corrupt audio file is repaired; invalid metadata is not ignored.
    temporary = safe_path(root, episode['podcaster_id'], episode['show_id'], key + '.part')
    for attempt in range(attempts):
        try:
            with (opener or open_http)(episode['enclosure_url']) as response:
                kind = response.headers.get('Content-Type', '').split(';')[0].lower().strip()
                if kind not in ('application/octet-stream', 'binary/octet-stream', '') and AUDIO_FORMATS.get(kind, (None,))[0] != extension:
                    raise ValueError(f'音檔回應格式不符 {extension}: {kind}')
                raw_length = response.headers.get('Content-Length')
                length = int(raw_length) if raw_length is not None else None
                if length is not None and (length <= 0 or length > max_bytes):
                    raise ValueError('音檔大小為零或超過單集限制')
                total, prefix = 0, b''
                sha, md5 = hashlib.sha256(), hashlib.md5()
                with temporary.open('wb') as file:
                    while block := response.read(1024 * 1024):
                        total += len(block)
                        if total > max_bytes:
                            raise ValueError('音檔超過單集大小限制')
                        prefix = (prefix + block)[:10] if len(prefix) < 10 else prefix
                        sha.update(block)
                        md5.update(block)
                        file.write(block)
                    file.flush()
                    os.fsync(file.fileno())
                if length is not None and total != length:
                    raise ValueError(f'音檔不完整: expected {length}, received {total}')
                valid_header = looks_like_mp3(prefix) if extension == 'mp3' else prefix[4:8] == b'ftyp'
                if total < 10 or not valid_header:
                    raise ValueError(f'下載內容缺少 {extension} 標頭')
            os.replace(temporary, destination)
            data = dict(episode, schema_version=1, local_file=destination.name,
                        downloaded_at=now(), bytes=total, sha256=sha.hexdigest(), md5=md5.hexdigest(), uploads={})
            atomic_json(manifest, data)
            return manifest, 'downloaded'
        except (OSError, HTTPException):
            if attempt + 1 == attempts:
                raise
            time.sleep(retry_delay * (attempt + 1))
        finally:
            temporary.unlink(missing_ok=True)
