import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import Mock, patch

from storysonic.catalog import parse_feed
from storysonic.download import download_episode, read_manifest
from storysonic.processing import process_episode, completed_artifacts, validate_segments
from test_catalog import SHOW, feed, item
from test_download import Response


class FakeEngine:
    recipe = {'backend': 'test', 'model_sha256': 'a' * 64, 'engine_version': '1', 'language': 'auto'}
    def __init__(self):
        self.calls = 0

    def transcribe(self, audio):
        self.calls += 1
        return {'language': 'zh', 'segments': [{'start': 0, 'end': 1.25, 'text': '侦探来了'}]}


class ProcessingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'content'
        self.manifest, _ = download_episode(parse_feed(feed(item()), SHOW)[0], self.root, opener=lambda _: Response())
        self.engine = FakeEngine()

    def process(self, **kwargs):
        with patch('storysonic.processing.audio_duration', return_value=2), \
                patch('storysonic.processing.convert_text', side_effect=lambda text: text.replace('侦', '偵').replace('来', '來')):
            return process_episode(self.manifest, self.root, engine=self.engine, traditional=True, **kwargs)

    def test_transcript_outputs_and_moved_content_skip(self):
        completion, status = self.process()
        self.assertEqual(status, 'transcribed')
        transcript = json.loads((completion.parent / 'transcript.json').read_text())
        self.assertFalse(transcript['reviewed'])
        self.assertEqual(transcript['segments'][0]['raw_text'], '侦探来了')
        self.assertEqual((completion.parent / 'transcript.txt').read_text(), '偵探來了\n')
        self.assertIn('00:00:01,250', (completion.parent / 'transcript.srt').read_text())
        moved = self.root.parent / 'moved'
        shutil.copytree(self.root, moved)
        old = self.root
        self.root = moved
        self.manifest = moved / self.manifest.relative_to(old)
        self.assertEqual(self.process()[1], 'transcript_skipped')
        self.assertEqual(self.engine.calls, 1)
        self.assertNotIn(str(old), completion.read_text())

    def test_corrupt_output_rebuilt_and_changed_recipe_separate(self):
        completion, _ = self.process()
        (completion.parent / 'transcript.txt').write_text('broken')
        self.assertEqual(self.process()[1], 'transcribed')
        self.engine.recipe = dict(self.engine.recipe, engine_version='2')
        second, _ = self.process()
        self.assertNotEqual(completion, second)
        self.assertEqual(len(completed_artifacts(self.manifest, self.root)), 2)

    def test_failure_never_commits_and_invalid_times_fail(self):
        self.engine.transcribe = Mock(side_effect=RuntimeError('backend failure'))
        with self.assertRaises(RuntimeError):
            self.process()
        self.assertEqual(list(self.root.rglob('complete.json')), [])
        for value in [float('nan'), float('inf'), -1, 3]:
            with self.assertRaises(ValueError):
                validate_segments([{'start': value, 'end': 2, 'text': 'bad'}], 2)

    def test_wav_conversion_preserves_source_and_failure_is_incomplete(self):
        original = self.manifest.with_suffix('.mp3').read_bytes()
        def convert(source, destination):
            destination.write_bytes(b'RIFF' + b'wav-data' * 20)
        with patch('storysonic.processing.audio_duration', return_value=2), \
                patch('storysonic.processing.ffmpeg_version', return_value='test'), \
                patch('storysonic.processing.convert_wav', side_effect=convert):
            result, status = process_episode(self.manifest, self.root)
            self.assertEqual(status, 'converted')
            self.assertEqual(process_episode(self.manifest, self.root)[1], 'conversion_skipped')
        self.assertEqual(self.manifest.with_suffix('.mp3').read_bytes(), original)
        (result.parent / 'audio.wav').unlink()
        with patch('storysonic.processing.audio_duration', return_value=2), \
                patch('storysonic.processing.ffmpeg_version', return_value='test'), \
                patch('storysonic.processing.convert_wav', side_effect=ValueError('decode')):
            with self.assertRaises(ValueError):
                process_episode(self.manifest, self.root)
        self.assertFalse(result.exists())

    def test_tampered_completion_paths_are_rejected(self):
        completion, _ = self.process()
        data = json.loads(completion.read_text())
        data['files']['../../outside'] = data['files'].pop('transcript.txt')
        completion.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            completed_artifacts(self.manifest, self.root)
