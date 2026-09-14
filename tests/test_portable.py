import io
import json
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch

from test_catalog import SHOW, feed, item
from test_download import Response

from storysonic.__main__ import main
from storysonic.catalog import parse_feed
from storysonic.download import download_episode, read_manifest


class PortableTests(unittest.TestCase):
    def test_m4a_download_and_legacy_mp3(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for mime in ('audio/mp4', 'audio/m4a', 'audio/x-m4a'):
                episode = parse_feed(feed(item(guid=mime).replace('audio/mpeg', mime)), SHOW)[0]
                audio = b'\x00\x00\x00\x18ftypM4A ' + b'x' * 50
                manifest, _ = download_episode(episode, root, opener=lambda _: Response(audio, kind=mime))  # noqa: B023
                data = read_manifest(manifest, root)
                self.assertTrue(data['local_file'].endswith('.m4a'))
                self.assertEqual(data['media_type'], 'audio/mp4')
            ep = parse_feed(feed(item()), SHOW)[0]
            manifest, _ = download_episode(ep, root, opener=lambda _: Response())
            data = json.loads(manifest.read_text())
            data.pop('media_type', None); data.pop('extension', None)
            manifest.write_text(json.dumps(data))
            self.assertEqual(download_episode(ep, root, opener=Mock(side_effect=AssertionError()))[1], 'skipped')

    def test_all_shows_feed_failure_continues_and_dry_run_has_no_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / 'podcasts.toml'
            shutil.copyfile('podcasts.toml', config)
            root = Path(tmp) / 'content'
            output = io.StringIO()
            def fetch(show):
                if show.id == 'detective-pig':
                    raise OSError('offline')
                return parse_feed(feed(item()), show)
            with patch('storysonic.__main__.fetch_episodes', side_effect=fetch), redirect_stdout(output):
                code = main(['download', '--all-shows', '--all', '--dry-run', '--config', str(config), '--content-dir', str(root)])
            events = [json.loads(x) for x in output.getvalue().splitlines()]
            self.assertEqual(code, 1)
            self.assertEqual(sum(e['event'] == 'planned' for e in events), 11)
            self.assertFalse(root.exists())

    def test_low_space_stops_before_download(self):
        with tempfile.TemporaryDirectory() as tmp, redirect_stdout(io.StringIO()):
            with patch('storysonic.__main__.fetch_episodes', return_value=parse_feed(feed(item()), SHOW)), \
                    patch('shutil.disk_usage', return_value=Mock(free=1)), \
                    patch('storysonic.__main__.download_episode') as download:
                code = main(['download', '--show', 'detective-pig', '--content-dir', tmp])
            self.assertEqual(code, 1)
            download.assert_not_called()

    def test_corrupt_manifest_does_not_hide_other_local_episodes(self):
        with tempfile.TemporaryDirectory() as tmp, redirect_stdout(io.StringIO()):
            root = Path(tmp)
            good, _ = download_episode(parse_feed(feed(item()), SHOW)[0], root, opener=lambda _: Response())
            (good.parent / 'bad.json').write_text('{')
            with patch('storysonic.drive.DriveUploader.upload', return_value={'status': 'skipped'}) as upload:
                code = main(['upload', '--show', 'detective-pig', '--all', '--content-dir', tmp])
            self.assertEqual(code, 1)
            self.assertEqual(upload.call_count, 1)

    def test_sigterm_interrupts_and_releases_lock(self):
        import signal

        from storysonic.download import content_lock
        with tempfile.TemporaryDirectory() as tmp, redirect_stdout(io.StringIO()):
            with patch('storysonic.__main__.fetch_episodes', return_value=parse_feed(feed(item()), SHOW)), \
                    patch('storysonic.__main__.download_episode', side_effect=lambda *a, **k: signal.raise_signal(signal.SIGTERM)):
                code = main(['download', '--show', 'detective-pig', '--content-dir', tmp])
            self.assertEqual(code, 130)
            with content_lock(tmp):
                pass
