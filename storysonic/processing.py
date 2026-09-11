"""Per-episode, portable derived artifacts. Callers hold the content lock."""

import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import tempfile

from .download import atomic_json, file_hashes, now, read_manifest, safe_path, verified_file


def fingerprint(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def ffmpeg_version():
    return command(['ffmpeg', '-version']).splitlines()[0]


def command(args):
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=7200)
    except FileNotFoundError as exc:
        raise ValueError('找不到 ffmpeg/ffprobe；請先執行安裝腳本或使用 Docker') from exc
    except subprocess.TimeoutExpired as exc:
        raise ValueError('音訊解碼逾時（2 小時）') from exc
    if result.returncode:
        raise ValueError(f'{args[0]} 失敗 (exit {result.returncode}): {result.stderr[-2000:]}')
    return result.stdout


def audio_duration(audio):
    value = float(command(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                           '-of', 'default=noprint_wrappers=1:nokey=1', str(audio)]).strip())
    if not math.isfinite(value) or value <= 0:
        raise ValueError('音檔長度必須為有限正數')
    return value


def convert_wav(audio, destination):
    command(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', str(audio), '-map', '0:a:0',
             '-vn', '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le', '-f', 'wav', str(destination)])


def convert_text(text):
    try:
        from opencc import OpenCC
    except ImportError as exc:
        raise ValueError('繁體轉換需安裝 opencc-python-reimplemented；請重新執行安裝腳本') from exc
    return OpenCC('s2twp').convert(text)


def validate_segments(segments, duration):
    if not isinstance(segments, list):
        raise ValueError('轉錄 segments 必須為陣列')
    previous = 0.0
    result = []
    for segment in segments:
        start, end = float(segment['start']), float(segment['end'])
        text = segment['text']
        if (not math.isfinite(start) or not math.isfinite(end) or start < previous or end < start
                or start > duration or end > duration + 1 or not isinstance(text, str)):
            raise ValueError('轉錄時間碼或文字無效')
        previous = start
        result.append({'start': round(start, 3), 'end': round(min(end, duration), 3), 'raw_text': text.strip()})
    return result


def srt_time(seconds):
    ms = round(seconds * 1000)
    hours, ms = divmod(ms, 3600000)
    minutes, ms = divmod(ms, 60000)
    seconds, ms = divmod(ms, 1000)
    return f'{hours:02}:{minutes:02}:{seconds:02},{ms:03}'


def derived_directory(root, data, recipe_id=None):
    parts = [data['podcaster_id'], data['show_id'], 'derived', data['episode_key']]
    if recipe_id is not None:
        if not re.fullmatch('[0-9a-f]{64}', recipe_id):
            raise ValueError('recipe ID 無效')
        parts.append(recipe_id)
    return safe_path(root, *parts)


def verify_completion(path, data, root):
    path = Path(path)
    safe_path(root, *path.absolute().relative_to(Path(root).absolute()).parts)
    record = json.loads(path.read_text(encoding='utf-8'))
    if (record.get('schema_version') != 1 or record.get('episode_key') != data['episode_key']
            or record.get('source_sha256') != data['sha256']
            or fingerprint(record.get('recipe')) != path.parent.name
            or path.parent != derived_directory(root, data, path.parent.name)):
        raise ValueError('衍生物 identity 或來源雜湊不符')
    kind = record['recipe'].get('kind')
    expected = {'transcript.txt', 'transcript.srt', 'transcript.json'} if kind == 'transcript' else {'audio.wav'}
    if kind not in ('transcript', 'wav') or set(record.get('files', {})) != expected:
        raise ValueError('衍生物檔案清單無效')
    for name, hashes in record['files'].items():
        file = safe_path(root, *path.parent.relative_to(Path(root).absolute()).parts, name)
        if file_hashes(file) != hashes:
            raise ValueError(f'衍生物雜湊不符: {name}')
    return record


def completed_artifacts(manifest, root):
    root = Path(root).absolute()
    data = read_manifest(manifest, root)
    records = []
    for path in sorted(derived_directory(root, data).glob('*/complete.json')):
        record = verify_completion(path, data, root)
        if record['recipe']['kind'] == 'transcript':
            records.append((path, record))
    return records


def process_episode(manifest, root, *, engine=None, traditional=False):
    root = Path(root).absolute()
    data = read_manifest(manifest, root)
    audio = verified_file(manifest, data, root)
    kind = 'transcript' if engine else 'wav'
    recipe = {'schema_version': 1, 'kind': kind, 'source_sha256': data['sha256']}
    if engine:
        recipe.update(engine=engine.recipe, traditional=traditional, text_conversion='s2twp-v0.1.7' if traditional else None)
    else:
        recipe.update(ffmpeg=ffmpeg_version(), sample_rate=16000, channels=1, codec='pcm_s16le')
    directory = derived_directory(root, data, fingerprint(recipe))
    directory.mkdir(parents=True, exist_ok=True)
    completion = safe_path(root, *directory.relative_to(root).parts, 'complete.json')
    if completion.exists():
        try:
            verify_completion(completion, data, root)
            return completion, 'transcript_skipped' if engine else 'conversion_skipped'
        except (ValueError, OSError, KeyError, TypeError):
            # Completion is the commit marker; invalidate it before repairing any file.
            completion.unlink()
    duration = audio_duration(audio)
    with tempfile.TemporaryDirectory(prefix='.processing-', dir=directory) as tmp:
        temporary = Path(tmp)
        if engine:
            raw = engine.transcribe(audio)
            segments = validate_segments(raw['segments'], duration)
            for segment in segments:
                segment['text'] = convert_text(segment['raw_text']) if traditional else segment['raw_text']
            result = {'schema_version': 1, 'episode_key': data['episode_key'], 'title': data['title'],
                      'source_sha256': data['sha256'], 'source_url': data['enclosure_url'], 'recipe': recipe,
                      'language': raw.get('language'), 'duration_seconds': duration,
                      'created_at': now(), 'reviewed': False, 'segments': segments}
            atomic_json(temporary / 'transcript.json', result)
            (temporary / 'transcript.txt').write_text('\n'.join(s['text'] for s in segments) + '\n', encoding='utf-8')
            srt = '\n'.join(f"{i}\n{srt_time(s['start'])} --> {srt_time(s['end'])}\n{s['text']}\n"
                            for i, s in enumerate(segments, 1))
            (temporary / 'transcript.srt').write_text(srt, encoding='utf-8')
        else:
            convert_wav(audio, temporary / 'audio.wav')
        files = {}
        for source in sorted(temporary.iterdir()):
            target = safe_path(root, *directory.relative_to(root).parts, source.name)
            files[source.name] = file_hashes(source)
            os.replace(source, target)
        record = {'schema_version': 1, 'episode_key': data['episode_key'], 'source_sha256': data['sha256'],
                  'recipe': recipe, 'created_at': now(), 'files': files, 'uploads': {}}
        atomic_json(completion, record)
    return completion, 'transcribed' if engine else 'converted'
