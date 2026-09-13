"""Google Drive integration through the user's authenticated gws CLI."""

import json
from pathlib import Path
import re
import subprocess
from urllib.parse import urlsplit

from .download import atomic_json, now, read_manifest, verified_file


FOLDER = 'application/vnd.google-apps.folder'
FILE_FIELDS = 'id,name,mimeType,parents,trashed,size,md5Checksum,webViewLink,appProperties'


def folder_id(value):
    if '://' in value:
        parsed = urlsplit(value)
        if parsed.scheme != 'https' or parsed.netloc != 'drive.google.com':
            raise ValueError('Drive 資料夾 URL 必須來自 https://drive.google.com')
        match = re.fullmatch(r'/drive/(?:u/\d+/)?folders/([A-Za-z0-9_-]+)/?', parsed.path)
        value = match.group(1) if match else ''
    if not re.fullmatch(r'[A-Za-z0-9_-]+', value) or value == 'root':
        raise ValueError('請指定 Drive folder ID 或資料夾網址，不接受 root 別名')
    return value


def quote(value):
    return "'" + value.replace('\\', '\\\\').replace("'", "\\'") + "'"


def display_name(value, stable_id):
    clean = re.sub(r'[\x00-\x1f/\\]', '_', value).strip()[:100]
    return f'{clean} [{stable_id}]'


class GwsClient:
    def __init__(self, binary='gws', runner=None):
        self.binary = binary
        self.runner = runner or subprocess.run

    def call(self, method, params, body=None, upload=None):
        params = dict(params, supportsAllDrives=True)
        args = [self.binary, 'drive', 'files', method, '--params', json.dumps(params), '--format', 'json']
        if body is not None:
            args += ['--json', json.dumps(body, ensure_ascii=False)]
        if upload is not None:
            args += ['--upload', str(Path(upload).absolute())]
        try:
            result = self.runner(args, capture_output=True, text=True, timeout=300)
        except FileNotFoundError as exc:
            raise ValueError('找不到 gws，請安裝 Google Workspace CLI 並執行 gws auth login -s drive') from exc
        except subprocess.TimeoutExpired as exc:
            raise ValueError('gws 逾時，遠端結果未確認；請重跑 upload，工具會先查遠端避免重複建立') from exc
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            detail = (result.stderr or result.stdout).strip()[:800]
            raise ValueError(f'gws 未回傳有效 JSON (exit {result.returncode}): {detail}') from exc
        if result.returncode or not isinstance(data, dict) or 'error' in data:
            error = data.get('error', data) if isinstance(data, dict) else data
            message = error.get('message', str(error)) if isinstance(error, dict) else str(error)
            guidance = '；請執行 gws auth login -s drive 後重試' if any(s in message.lower() for s in ('invalid_grant', 'auth', 'token', 'credential')) else ''
            raise ValueError(f'gws {method} 失敗 (exit {result.returncode}): {message[:800]}{guidance}')
        return data

    def find(self, query, drive_id=None):
        params = {'q': query + ' and trashed=false', 'pageSize': 100,
                  'fields': f'nextPageToken,files({FILE_FIELDS})', 'includeItemsFromAllDrives': True}
        if drive_id:
            params.update(corpora='drive', driveId=drive_id)
        files, tokens = [], set()
        while True:
            page = self.call('list', params)
            files.extend(page.get('files', []))
            token = page.get('nextPageToken')
            if not token:
                return files
            if token in tokens:
                raise ValueError('Drive 回傳重複分頁 token，無法確認完整查詢結果')
            tokens.add(token)
            params['pageToken'] = token


class DriveUploader:
    def __init__(self, destination, client=None):
        self.root_id = folder_id(destination)
        self.client = client or GwsClient()
        self.drive_id = None
        self.ready = False
        self.folders = {}

    def check_root(self):
        if self.ready:
            return
        root = self.client.call('get', {'fileId': self.root_id, 'fields': 'id,name,mimeType,trashed,driveId,capabilities(canAddChildren)'})
        if root.get('mimeType') != FOLDER or root.get('trashed'):
            raise ValueError('指定的 Drive 目的地不是有效資料夾')
        if root.get('capabilities', {}).get('canAddChildren') is not True:
            raise ValueError('目前 gws 帳號沒有此 Drive 資料夾的寫入權限')
        self.drive_id = root.get('driveId')
        self.ready = True

    def ensure_folder(self, parent, name):
        cache_key = (parent, name)
        if cache_key in self.folders:
            return self.folders[cache_key]
        matches = self.client.find(f'{quote(parent)} in parents and name={quote(name)} and mimeType={quote(FOLDER)}', self.drive_id)
        if len(matches) > 1:
            raise ValueError(f'Drive 資料夾重複: {name}；請先整理重複資料夾')
        result = matches[0] if matches else self.client.call('create', {'fields': 'id,name,parents,mimeType'}, {'name': name, 'mimeType': FOLDER, 'parents': [parent]})
        if not result.get('id'):
            raise ValueError('Drive 未回傳資料夾 ID')
        self.folders[cache_key] = result['id']
        return result['id']

    def upload(self, manifest, content_root):
        data = read_manifest(manifest, content_root)
        file = verified_file(manifest, data, content_root)
        self.check_root()
        publisher = self.ensure_folder(self.root_id, display_name(data['podcaster_name'], data['podcaster_id']))
        show = self.ensure_folder(publisher, display_name(data['show_name'], data['show_id']))
        key = data['episode_key']
        matches = self.client.find(f"{quote(show)} in parents and appProperties has {{ key='storysonic_episode' and value={quote(key)} }}", self.drive_id)
        if len(matches) > 1:
            raise ValueError(f'Drive 同一單集有重複檔案: {key}；未覆寫任何檔案')
        status = 'skipped' if matches else 'uploaded'
        if matches:
            result = matches[0]
        else:
            title = re.sub(r'[\x00-\x1f/\\]', '_', data['title']).strip()[:100]
            body = {'name': f"{title}--{key}{file.suffix}", 'mimeType': data.get('media_type', 'audio/mpeg'), 'parents': [show],
                    'appProperties': {'storysonic_episode': key, 'storysonic_sha256': data['sha256']}}
            # Do not retry create here. A timeout can mean the file already exists.
            result = self.client.call('create', {'fields': 'id'}, body, upload=file)
        if not result.get('id'):
            raise ValueError('Drive 未回傳音檔 ID；上傳結果未確認')
        remote = self.client.call('get', {'fileId': result['id'], 'fields': FILE_FIELDS})
        if (remote.get('trashed') or show not in remote.get('parents', [])
                or remote.get('size') != str(data['bytes']) or remote.get('md5Checksum') != data['md5']
                or remote.get('appProperties', {}).get('storysonic_episode') != key):
            raise ValueError(f"Drive 核對失敗或內容衝突: {result['id']}；未記錄成功、未覆寫遠端")
        record = {'file_id': result['id'], 'folder_id': show, 'root_id': self.root_id,
                  'url': remote.get('webViewLink'), 'verified_at': now(), 'md5': remote['md5Checksum'], 'bytes': data['bytes']}
        data['uploads'][self.root_id] = record
        atomic_json(manifest, data)
        return dict(record, status=status)

    def upload_transcripts(self, manifest, content_root):
        from .processing import completed_artifacts
        data = read_manifest(manifest, content_root)
        verified_file(manifest, data, content_root)
        completions = completed_artifacts(manifest, content_root)
        if not completions:
            raise ValueError('沒有已完成逐字稿；請先執行 transcribe')
        self.check_root()
        publisher = self.ensure_folder(self.root_id, display_name(data['podcaster_name'], data['podcaster_id']))
        show = self.ensure_folder(publisher, display_name(data['show_name'], data['show_id']))
        transcripts = self.ensure_folder(show, 'transcripts')
        episode = self.ensure_folder(transcripts, data['episode_key'])
        results = []
        for completion, record in completions:
            parent = self.ensure_folder(episode, completion.parent.name)
            for name, hashes in record['files'].items():
                identity = f"{data['episode_key']}:{completion.parent.name}:{name}"
                matches = self.client.find(f"{quote(parent)} in parents and appProperties has {{ key='storysonic_artifact' and value={quote(identity)} }}", self.drive_id)
                if len(matches) > 1:
                    raise ValueError(f'Drive 逐字稿檔案重複: {name}')
                status = 'skipped' if matches else 'uploaded'
                if matches:
                    result = matches[0]
                else:
                    mime = {'transcript.txt': 'text/plain', 'transcript.srt': 'application/x-subrip',
                            'transcript.json': 'application/json'}[name]
                    result = self.client.call('create', {'fields': 'id'},
                        {'name': name, 'mimeType': mime, 'parents': [parent],
                         'appProperties': {'storysonic_artifact': identity, 'storysonic_sha256': hashes['sha256']}},
                        upload=completion.parent / name)
                if not result.get('id'):
                    raise ValueError('Drive 未回傳逐字稿 ID；請重跑 upload 核對')
                remote = self.client.call('get', {'fileId': result['id'], 'fields': FILE_FIELDS})
                if (remote.get('trashed') or parent not in remote.get('parents', [])
                        or remote.get('size') != str(hashes['bytes']) or remote.get('md5Checksum') != hashes['md5']
                        or remote.get('appProperties', {}).get('storysonic_artifact') != identity):
                    raise ValueError(f'Drive 逐字稿核對失敗: {name}；未覆寫遠端')
                saved = {'file_id': result['id'], 'folder_id': parent, 'verified_at': now(),
                         'url': remote.get('webViewLink'), 'md5': hashes['md5'], 'bytes': hashes['bytes']}
                record.setdefault('uploads', {}).setdefault(self.root_id, {})[name] = saved
                atomic_json(completion, record)
                results.append(dict(saved, status=status, name=name))
        return results
