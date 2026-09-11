import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from storysonic.catalog import parse_feed
from storysonic.download import content_lock, download_episode, read_manifest, verified_file
from test_catalog import SHOW, feed, item


AUDIO = b'ID3\x04\x00\x00\x00\x00\x00\x00' + b'audio' * 100


class Response(io.BytesIO):
    def __init__(self, data=AUDIO, length=None, kind='audio/mpeg'):
        super().__init__(data)
        self.headers = {'Content-Length': str(len(data) if length is None else length), 'Content-Type': kind}


class DownloadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'content'
        self.episode = parse_feed(feed(item()), SHOW)[0]

    def get(self, **kwargs):
        return download_episode(self.episode, self.root, opener=lambda url: Response(), **kwargs)

    def test_complete_download_manifest_and_rerun_skip(self):
        manifest, status = self.get()
        self.assertEqual(status, 'downloaded')
        data = read_manifest(manifest, self.root, SHOW)
        file = verified_file(manifest, data, self.root)
        self.assertEqual(file.read_bytes(), AUDIO)
        self.assertEqual(data['guid'], 'g1')
        self.assertEqual(data['bytes'], len(AUDIO))
        self.assertNotIn(str(self.root), manifest.read_text())
        opener = Mock(side_effect=AssertionError('audio GET must be skipped'))
        self.assertEqual(download_episode(self.episode, self.root, opener=opener)[1], 'skipped')

    def test_corruption_is_redownloaded(self):
        manifest, _ = self.get()
        manifest.with_suffix('.mp3').write_bytes(b'broken')
        self.assertEqual(self.get()[1], 'downloaded')
        self.assertEqual(manifest.with_suffix('.mp3').read_bytes(), AUDIO)

    def test_incomplete_and_non_audio_responses_leave_no_success(self):
        for response in [lambda: Response(length=9999), lambda: Response(b'<html>login</html>', kind='text/html'), lambda: Response(b'not mp3')]:
            with self.subTest(response=response), self.assertRaises(ValueError):
                download_episode(self.episode, self.root, opener=lambda url: response(), attempts=1)
            self.assertEqual(list(self.root.rglob('*.mp3')), [])
            self.assertEqual(list(self.root.rglob('*.json')), [])
            self.assertEqual(list(self.root.rglob('*.part')), [])

    def test_size_limit_and_retry(self):
        with self.assertRaises(ValueError):
            self.get(max_bytes=10, attempts=1)
        opener = Mock(side_effect=[OSError('offline'), Response()])
        _, status = download_episode(self.episode, self.root, opener=opener, retry_delay=0)
        self.assertEqual(status, 'downloaded')
        self.assertEqual(opener.call_count, 2)

    def test_unknown_content_length_still_enforces_stream_limit(self):
        response = Response()
        del response.headers['Content-Length']
        with self.assertRaises(ValueError):
            download_episode(self.episode, self.root, opener=lambda url: response, max_bytes=100, attempts=1)
        self.assertEqual(list(self.root.rglob('*.mp3')), [])
        self.assertEqual(list(self.root.rglob('*.part')), [])

    def test_manifest_path_escape_and_symlink_rejected(self):
        manifest, _ = self.get()
        data = json.loads(manifest.read_text())
        data['local_file'] = '../../../outside.mp3'
        manifest.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            read_manifest(manifest, self.root, SHOW)
        manifest.unlink()
        file = manifest.with_suffix('.mp3')
        file.unlink()
        outside = Path(self.temp.name) / 'outside.mp3'
        outside.write_bytes(b'private')
        file.symlink_to(outside)
        with self.assertRaises(ValueError):
            self.get()
        self.assertEqual(outside.read_bytes(), b'private')

    def test_process_lock_prevents_parallel_writers_and_releases(self):
        with content_lock(self.root):
            with self.assertRaises(ValueError):
                with content_lock(self.root):
                    self.fail('second lock granted')
        with content_lock(self.root):
            pass
