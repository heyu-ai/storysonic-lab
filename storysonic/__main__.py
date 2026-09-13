"""Installable podcast collection, conversion, transcription and upload CLI."""

import argparse
from contextlib import nullcontext
from dataclasses import asdict
from http.client import HTTPException
import json
from pathlib import Path
import shutil
import signal
import sys

from .catalog import fetch_episodes, load_config, select_episodes
from .download import content_lock, download_episode, read_manifest, safe_path, verified_file
from .drive import DriveUploader, folder_id


def positive_int(value):
    try:
        number = int(value)
        if number <= 0:
            raise ValueError()
        return number
    except ValueError as exc:
        raise argparse.ArgumentTypeError('必須為正整數；全部請使用 --all') from exc


def parser():
    root = argparse.ArgumentParser(description='Podcast 下載、轉檔、逐字稿與 Google Drive 上傳')
    commands = root.add_subparsers(dest='command', required=True)
    for name, help_text in [('list', '列出設定節目或 RSS 單集'), ('download', '下載 MP3/M4A'),
                            ('upload', '上傳本機音檔與選配逐字稿'), ('transcribe', '音檔轉逐字稿'),
                            ('convert', '音檔轉 16 kHz mono WAV，保留原檔')]:
        cmd = commands.add_parser(name, help=help_text)
        cmd.add_argument('--config', type=Path, default=Path('podcasts.toml'), help='預設目前目錄 podcasts.toml')
        cmd.add_argument('--content-dir', type=Path, default=Path('content'))
        shows = cmd.add_mutually_exclusive_group(required=name != 'list')
        shows.add_argument('--show', help='podcasts.toml 內的節目 ID')
        shows.add_argument('--all-shows', action='store_true', help='選取設定檔全部節目')
        cmd.add_argument('--match', default='', help='標題包含此字串')
        scope = cmd.add_mutually_exclusive_group()
        scope.add_argument('--limit', type=positive_int, default=3, help='每個節目最多幾集，預設 3')
        scope.add_argument('--all', action='store_true', help='明確選取全部符合單集')
        if name != 'list':
            cmd.add_argument('--dry-run', action='store_true', help='只列計畫，不寫入或下載模型')
            cmd.add_argument('--reserve-gb', type=positive_int, default=5, help='每集開始前保留至少幾 GiB 空間')
        if name in ('download', 'upload'):
            cmd.add_argument('--drive-folder', help='Drive 資料夾 ID 或 URL，覆寫設定')
        if name == 'upload':
            cmd.add_argument('--include-transcripts', action='store_true', help='加上已完成的 TXT/SRT/JSON 逐字稿')
        if name == 'download':
            cmd.add_argument('--upload', action='store_true', help='下載後上傳，預設只下載')
            cmd.add_argument('--max-mb', type=positive_int, default=256, help='單集上限 MiB，預設 256')
        if name == 'transcribe':
            cmd.add_argument('--backend', choices=['mlx', 'faster-whisper'], default='mlx')
            model = cmd.add_mutually_exclusive_group()
            model.add_argument('--model', help='Hugging Face 模型 repo ID；MLX 預設 large-v3-turbo，CPU 預設 small')
            model.add_argument('--model-dir', type=Path, help='已下載模型目錄；不另下載權重')
            cmd.add_argument('--cache-dir', type=Path, default=Path('data/models'))
            cmd.add_argument('--language', default='auto', help='auto、zh、en 等 Whisper 語言碼；不翻譯')
            cmd.add_argument('--traditional', action='store_true', help='TXT/SRT 轉繁體，JSON 另保留原始識別文字')
    return root


def emit(event, **fields):
    print(json.dumps(dict(event=event, **fields), ensure_ascii=False), flush=True)


def local_episodes(show, root, on_error=None):
    directory = safe_path(root, show.podcaster_id, show.id)
    episodes = []
    for path in sorted(directory.glob('*.json')):
        try:
            data = read_manifest(path, root, show)
        except (ValueError, OSError) as exc:
            if on_error is None:
                raise
            on_error(path, exc)
            continue
        data['_manifest'] = path
        episodes.append(data)
    return episodes


ERRORS = (ValueError, OSError, HTTPException, RuntimeError)


def run(args):
    configured_folder, shows = load_config(args.config)
    if args.command == 'list' and not args.show and not args.all_shows:
        for show in shows.values():
            emit('show', **asdict(show))
        return 0
    if args.show and args.show not in shows:
        raise ValueError(f'未知 show: {args.show}；請先執行 python -m storysonic list')
    selected_shows = list(shows.values()) if args.all_shows else [shows[args.show]]
    upload_enabled = args.command == 'upload' or (args.command == 'download' and args.upload)
    destination = folder_id(args.drive_folder or configured_folder) if upload_enabled else None
    if args.command == 'download' and args.drive_folder and not args.upload:
        raise ValueError('--drive-folder 需搭配 --upload')
    dry = args.command == 'list' or args.dry_run
    uploader = None if dry or not upload_enabled else DriveUploader(destination)
    engine = None
    counts = dict(selected=0, downloaded=0, skipped=0, uploaded=0, upload_skipped=0, failed=0)
    if args.command in ('transcribe', 'convert'):
        counts.update(transcribed=0, transcript_skipped=0, converted=0, conversion_skipped=0)
    with nullcontext() if dry else content_lock(args.content_dir):
        for show in selected_shows:
            def manifest_error(path, exc):
                counts['failed'] += 1
                emit('error', show=show.id, manifest=str(path), message=str(exc))
            try:
                source = (fetch_episodes(show) if args.command in ('list', 'download')
                          else local_episodes(show, args.content_dir, manifest_error))
                selected = select_episodes(source, args.match, None if args.all else args.limit)
                if not selected:
                    raise ValueError('沒有符合的單集；請確認篩選條件，或先執行 download')
            except ERRORS as exc:
                counts['failed'] += 1
                emit('error', show=show.id, message=str(exc))
                continue
            counts['selected'] += len(selected)
            for episode in selected:
                try:
                    if args.command == 'list':
                        emit('episode', **episode)
                        continue
                    if dry:
                        if args.command != 'download':
                            verified_file(episode['_manifest'], episode, args.content_dir)
                        emit('planned', show=show.id, title=episode['title'], episode_key=episode['episode_key'],
                             action=args.command, local_directory=str(args.content_dir / show.podcaster_id / show.id),
                             drive_folder=destination)
                        continue
                    # Reserve a whole prospective download in addition to the requested free floor.
                    extra = args.max_mb * 1024 * 1024 if args.command == 'download' else 0
                    if shutil.disk_usage(args.content_dir).free < args.reserve_gb * 1024 ** 3 + extra:
                        emit('error', show=show.id, message='可用空間低於保留量；停止批次，釋放空間後重跑')
                        counts['failed'] += 1
                        emit('summary', **counts)
                        return 1
                    if args.command == 'download':
                        manifest, status = download_episode(episode, args.content_dir, max_bytes=args.max_mb * 1024 * 1024)
                        counts[status] += 1
                        emit(status, title=episode['title'], manifest=str(manifest))
                    else:
                        manifest = episode['_manifest']
                    if args.command in ('transcribe', 'convert'):
                        from .processing import process_episode
                        # Initialize once per worker, only after selection and dry-run handling.
                        if args.command == 'transcribe' and engine is None:
                            from .engines import Engine
                            emit('model_loading', backend=args.backend)
                            engine = Engine(args.backend, model=args.model, model_dir=args.model_dir,
                                            cache_dir=args.cache_dir, language=args.language)
                        emit('processing', show=show.id, title=episode['title'], episode_key=episode['episode_key'])
                        result, status = process_episode(manifest, args.content_dir, engine=engine,
                                                         traditional=getattr(args, 'traditional', False))
                        counts[status] += 1
                        emit(status, title=episode['title'], completion=str(result))
                    if uploader:
                        uploaded = uploader.upload(manifest, args.content_dir)
                        status = 'upload_skipped' if uploaded.pop('status') == 'skipped' else 'uploaded'
                        counts[status] += 1
                        emit(status, title=episode['title'], **uploaded)
                        if getattr(args, 'include_transcripts', False):
                            for record in uploader.upload_transcripts(manifest, args.content_dir):
                                emit('transcript_upload', title=episode['title'], **record)
                except ERRORS as exc:
                    counts['failed'] += 1
                    emit('error', show=show.id, title=episode['title'], message=str(exc))
    # Keep existing single-show dry-run output compatible while reporting batch failures.
    if args.command != 'list' and (not dry or args.all_shows):
        emit('summary', **counts)
    return int(counts['failed'] > 0)


def stop(signum, frame):
    raise KeyboardInterrupt()


def main(argv=None):
    args = parser().parse_args(argv)
    previous = signal.signal(signal.SIGTERM, stop)
    try:
        return run(args)
    except ERRORS as exc:
        emit('error', message=str(exc))
        return 1
    except KeyboardInterrupt:
        emit('error', message='已中止；可重跑命令，工具會核對已完成檔案；未完成單集會重做')
        return 130
    finally:
        signal.signal(signal.SIGTERM, previous)


if __name__ == '__main__':
    sys.exit(main())
