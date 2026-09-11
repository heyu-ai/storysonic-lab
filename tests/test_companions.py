import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from storysonic.catalog import parse_feed
from storysonic.download import download_episode
from storysonic.drive import DriveUploader, GwsClient
from storysonic.processing import process_episode
from test_catalog import SHOW, feed, item
from test_download import Response
from test_drive import FakeGws
from test_processing import FakeEngine


class CompanionTests(unittest.TestCase):
    def test_transcripts_are_verified_and_repeat_upload_preserves_audio_lookup(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest, _ = download_episode(parse_feed(feed(item()), SHOW)[0], root, opener=lambda _: Response())
            fake = FakeGws()
            uploader = DriveUploader('root123', GwsClient(runner=fake))
            with self.assertRaisesRegex(ValueError, '逐字稿'):
                uploader.upload_transcripts(manifest, root)
            with patch('storysonic.processing.audio_duration', return_value=2):
                completion, _ = process_episode(manifest, root, engine=FakeEngine())
            first = uploader.upload_transcripts(manifest, root)
            self.assertEqual(len(first), 3)
            count = len(fake.files)
            self.assertTrue(all(r['status'] == 'skipped' for r in uploader.upload_transcripts(manifest, root)))
            self.assertEqual(len(fake.files), count)
            uploader.upload(manifest, root)
            self.assertEqual(uploader.upload(manifest, root)['status'], 'skipped')
            data = json.loads(completion.read_text())
            self.assertEqual(len(data['uploads']['root123']), 3)
            fake.fail_readback = True
            with self.assertRaisesRegex(ValueError, '核對'):
                uploader.upload_transcripts(manifest, root)
