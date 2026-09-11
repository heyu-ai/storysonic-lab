from contextlib import redirect_stdout, redirect_stderr
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from storysonic.__main__ import main
from storysonic.catalog import parse_feed
from test_catalog import SHOW, feed, item
from test_download import Response
from test_drive import FakeGws


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = self.root / 'podcasts.toml'
        self.config.write_text('''[drive]
folder = "root123"
[[shows]]
id = "detective-pig"
name = "豬探長"
podcaster_id = "ifkids"
podcaster_name = "如果兒童劇團"
feed_url = "https://example.com/feed"
''')
        self.common = ['--config', str(self.config), '--content-dir', str(self.root / 'content')]
        self.episodes = parse_feed(feed(item()), SHOW)

    def run_cli(self, *args):
        output = io.StringIO()
        with redirect_stdout(output), redirect_stderr(io.StringIO()):
            code = main([*args, *self.common])
        return code, [json.loads(line) for line in output.getvalue().splitlines()]

    def test_dry_run_never_writes_or_calls_drive(self):
        with patch('storysonic.__main__.fetch_episodes', return_value=self.episodes), patch('storysonic.drive.GwsClient.call', side_effect=AssertionError('Drive must not be called')):
            code, events = self.run_cli('download', '--show', 'detective-pig', '--dry-run', '--upload', '--drive-folder', 'override123')
        self.assertEqual(code, 0)
        self.assertEqual(events[0]['event'], 'planned')
        self.assertEqual(events[0]['drive_folder'], 'override123')
        self.assertFalse((self.root / 'content').exists())

    def test_download_and_standalone_upload_are_separate(self):
        with patch('storysonic.__main__.fetch_episodes', return_value=self.episodes), patch('storysonic.download.open_http', return_value=Response()), patch('storysonic.drive.GwsClient.call', side_effect=AssertionError('Drive must not be called')):
            code, events = self.run_cli('download', '--show', 'detective-pig')
        self.assertEqual(code, 0)
        self.assertEqual(events[0]['event'], 'downloaded')
        with patch('storysonic.drive.GwsClient.call', side_effect=AssertionError('dry-run must not call Drive')):
            code, events = self.run_cli('upload', '--show', 'detective-pig', '--dry-run')
        self.assertEqual(code, 0)
        self.assertEqual(events[0]['drive_folder'], 'root123')

    def test_unknown_show_and_empty_selection_return_nonzero(self):
        self.assertEqual(self.run_cli('download', '--show', 'missing')[0], 1)
        with patch('storysonic.__main__.fetch_episodes', return_value=[]):
            self.assertEqual(self.run_cli('download', '--show', 'detective-pig')[0], 1)

    def test_download_upload_then_standalone_upload_skips_remote(self):
        fake = FakeGws()
        with patch('storysonic.__main__.fetch_episodes', return_value=self.episodes), patch('storysonic.download.open_http', return_value=Response()), patch('storysonic.drive.subprocess.run', side_effect=fake):
            code, events = self.run_cli('download', '--show', 'detective-pig', '--upload')
            second_code, second_events = self.run_cli('upload', '--show', 'detective-pig')
        self.assertEqual(code, 0)
        self.assertEqual([e['event'] for e in events], ['downloaded', 'uploaded', 'summary'])
        self.assertEqual(second_code, 0)
        self.assertEqual(second_events[0]['event'], 'upload_skipped')
        self.assertEqual(len(fake.files), 4)

    def test_one_failure_allows_next_episode_but_batch_fails(self):
        episodes = parse_feed(feed(item(), item('g2')), SHOW)
        with patch('storysonic.__main__.fetch_episodes', return_value=episodes), patch('storysonic.download.open_http', side_effect=[Response(b'<html>bad</html>', kind='text/html'), Response()]):
            code, events = self.run_cli('download', '--show', 'detective-pig', '--all')
        self.assertEqual(code, 1)
        self.assertEqual([e['event'] for e in events], ['error', 'downloaded', 'summary'])

    def test_real_entrypoint_help_and_invalid_limit(self):
        for options in [['--help'], ['download', '--help']]:
            result = subprocess.run([sys.executable, '-m', 'storysonic', *options], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        for scope in [['--limit', '0'], ['--limit', '1', '--all']]:
            result = subprocess.run([sys.executable, '-m', 'storysonic', 'download', '--show', 'detective-pig', *self.common, *scope], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
