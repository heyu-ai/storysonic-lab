import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock

from storysonic.catalog import parse_feed
from storysonic.download import download_episode
from storysonic.drive import DriveUploader, GwsClient, folder_id
from test_catalog import SHOW, feed, item
from test_download import Response


class FakeGws:
    def __init__(self):
        self.root = 'root123'
        self.files = {self.root: {'id': self.root, 'name': 'Podcast', 'mimeType': 'application/vnd.google-apps.folder', 'driveId': 'shared1', 'capabilities': {'canAddChildren': True}}}
        self.calls = []
        self.fail_readback = False

    def __call__(self, args, **kwargs):
        self.calls.append(args)
        params = json.loads(args[args.index('--params') + 1])
        method = args[3]
        body = json.loads(args[args.index('--json') + 1]) if '--json' in args else {}
        if method == 'get':
            result = self.files[params['fileId']].copy()
            if self.fail_readback and result.get('md5Checksum'):
                result['md5Checksum'] = 'bad'
        elif method == 'list':
            q = params['q']
            files = []
            for file in self.files.values():
                if not any(f"'{p}' in parents" in q for p in file.get('parents', [])):
                    continue
                if 'appProperties has' in q:
                    props = file.get('appProperties', {})
                    matched = False
                    for prop_key, prop_val in props.items():
                        if f"key='{prop_key}'" in q and f"value='{prop_val}'" in q:
                            matched = True
                            break
                    if matched:
                        files.append(file.copy())
                elif f"name='{file['name']}'" in q:
                    files.append(file.copy())
            result = {'files': files}
        elif method == 'create':
            id_ = f'file{len(self.files)}'
            result = dict(body, id=id_, trashed=False, webViewLink=f'https://drive.google.com/file/d/{id_}/view')
            if '--upload' in args:
                data = Path(args[args.index('--upload') + 1]).read_bytes()
                result.update(size=str(len(data)), md5Checksum=hashlib.md5(data).hexdigest())
            self.files[id_] = result
        else:
            raise AssertionError(method)
        return subprocess.CompletedProcess(args, 0, json.dumps(result), '')


class DriveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest, _ = download_episode(parse_feed(feed(item()), SHOW)[0], self.root, opener=lambda url: Response())
        self.fake = FakeGws()
        self.client = GwsClient(runner=self.fake)

    def test_shared_drive_classification_and_remote_deduplication(self):
        uploader = DriveUploader('https://drive.google.com/drive/folders/root123?usp=sharing', self.client)
        first = uploader.upload(self.manifest, self.root)
        self.assertEqual(first['status'], 'uploaded')
        self.assertEqual(len(self.fake.files), 4)
        folders = [f['name'] for f in self.fake.files.values()]
        self.assertIn('如果兒童劇團 [ifkids]', folders)
        self.assertIn('豬探長 [detective-pig]', folders)
        # Lost local status must recover by querying Drive, not create another object.
        data = json.loads(self.manifest.read_text())
        data['uploads'] = {}
        self.manifest.write_text(json.dumps(data))
        second = uploader.upload(self.manifest, self.root)
        self.assertEqual(second['status'], 'skipped')
        self.assertEqual(len(self.fake.files), 4)
        self.assertIn('root123', json.loads(self.manifest.read_text())['uploads'])
        for args in self.fake.calls:
            params = json.loads(args[args.index('--params') + 1])
            self.assertTrue(params['supportsAllDrives'])
            if args[3] == 'list':
                self.assertEqual(params['driveId'], 'shared1')
                self.assertTrue(params['includeItemsFromAllDrives'])

    def test_remote_conflict_and_verification_failure_do_not_record_success(self):
        uploader = DriveUploader('root123', self.client)
        self.fake.fail_readback = True
        with self.assertRaisesRegex(ValueError, '核對'):
            uploader.upload(self.manifest, self.root)
        self.assertEqual(json.loads(self.manifest.read_text())['uploads'], {})
        with self.assertRaises(ValueError):
            uploader.upload(self.manifest, self.root)
        self.assertEqual(len(self.fake.files), 4)

    def test_local_corruption_prevents_any_drive_call(self):
        self.manifest.with_suffix('.mp3').write_bytes(b'broken')
        with self.assertRaises(ValueError):
            DriveUploader('root123', self.client).upload(self.manifest, self.root)
        self.assertEqual(self.fake.calls, [])

    def test_duplicate_folders_fail_without_creating_more(self):
        folder = {'name': '如果兒童劇團 [ifkids]', 'parents': ['root123'], 'mimeType': 'application/vnd.google-apps.folder'}
        self.fake.files.update({'a': dict(folder, id='a'), 'b': dict(folder, id='b')})
        with self.assertRaisesRegex(ValueError, '重複'):
            DriveUploader('root123', self.client).upload(self.manifest, self.root)
        self.assertEqual(len(self.fake.files), 3)

    def test_root_requires_write_permission(self):
        self.fake.files['root123']['capabilities']['canAddChildren'] = False
        with self.assertRaisesRegex(ValueError, '寫入'):
            DriveUploader('root123', self.client).upload(self.manifest, self.root)
        self.assertEqual(len(self.fake.files), 1)

    def test_paginated_listing(self):
        runner = Mock(side_effect=[subprocess.CompletedProcess([], 0, '{"files":[{"id":"a"}],"nextPageToken":"next"}', ''), subprocess.CompletedProcess([], 0, '{"files":[{"id":"b"}]}', '')])
        files = GwsClient(runner=runner).find("'root123' in parents", 'shared1')
        self.assertEqual([f['id'] for f in files], ['a', 'b'])
        args = runner.call_args_list[1].args[0]
        params = json.loads(args[args.index('--params') + 1])
        self.assertEqual(params['pageToken'], 'next')

    def test_auth_error_timeout_and_invalid_folder(self):
        runner = Mock(return_value=subprocess.CompletedProcess([], 1, '{"error":{"message":"invalid_grant"}}', ''))
        with self.assertRaisesRegex(ValueError, 'gws auth login'):
            GwsClient(runner=runner).call('get', {'fileId': 'x'})
        runner.side_effect = subprocess.TimeoutExpired('gws', 300)
        with self.assertRaisesRegex(ValueError, '逾時'):
            GwsClient(runner=runner).call('create', {})
        for value in ['', '../outside', 'https://evil.test/drive/folders/abc', 'root']:
            with self.assertRaises(ValueError):
                folder_id(value)
