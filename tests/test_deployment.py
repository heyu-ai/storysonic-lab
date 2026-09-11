from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest


class DeploymentTests(unittest.TestCase):
    def test_archive_excludes_data_and_secrets(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / 'source.tar.gz'
            result = subprocess.run([sys.executable, 'scripts/package.py', str(archive)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            with tarfile.open(archive) as tar:
                names = tar.getnames()
            self.assertIn('storysonic-lab/storysonic/__main__.py', names)
            self.assertIn('storysonic-lab/podcasts.toml', names)
            for name in names:
                self.assertFalse(any(p in name.split('/') for p in ('data', 'outputs', '.venv', '.git', '.env', 'credentials.json')))
                self.assertFalse(name.endswith(('.mp3', '.m4a', '.wav', '.pyc')))

    def test_docker_context_is_an_allowlist_and_shell_parses(self):
        ignore = Path('.dockerignore').read_text()
        self.assertTrue(ignore.startswith('**\n'))
        for script in ['scripts/setup-mac.sh', 'scripts/run-mac.sh']:
            result = subprocess.run(['bash', '-n', script], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        dockerfile = Path('Dockerfile').read_text()
        self.assertNotIn('COPY . ', dockerfile)
        self.assertIn('USER worker', dockerfile)
