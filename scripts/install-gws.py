"""Image-build helper: install the pinned, checksummed gws Linux binary."""
import hashlib
import io
from pathlib import Path
import platform
import tarfile
from urllib.request import urlopen

ARCHIVES = {
    'aarch64': ('aarch64', 'dcf4cf9f2b95c0c079aa48400487d48f1e90adc144e35436160ab85ddb59d3a9'),
    'x86_64': ('x86_64', '4b2dbc3b1716aa0cbfd91d59ea896dbf5e893a151594c363f0c98e760e2e5046'),
}
arch, expected = ARCHIVES[platform.machine()]
url = f'https://github.com/googleworkspace/cli/releases/download/v0.8.0/gws-{arch}-unknown-linux-gnu.tar.gz'
with urlopen(url, timeout=120) as response:
    data = response.read()
if hashlib.sha256(data).hexdigest() != expected:
    raise SystemExit('gws archive SHA-256 mismatch')
with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as tar:
    matches = [m for m in tar.getmembers() if Path(m.name).name == 'gws' and m.isfile()]
    if len(matches) != 1:
        raise SystemExit('gws archive has unexpected layout')
    target = Path('/usr/local/bin/gws')
    target.write_bytes(tar.extractfile(matches[0]).read())
    target.chmod(0o755)
