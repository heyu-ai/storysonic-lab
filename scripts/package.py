"""Create a source-only transfer archive, including uncommitted implementation."""
from pathlib import Path
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]
FILES = ['README.md', 'pyproject.toml', 'requirements-cpu.lock', 'uv.lock', 'podcasts.toml', 'Dockerfile',
         'compose.yaml', 'compose.drive.yaml', '.dockerignore', '.gitignore', 'Makefile',
         'AGENTS.md', 'CLAUDE.md', '.spectra.yaml', 'content/README.md']
DIRECTORIES = {'storysonic': '*.py', 'tests': '*.py', 'scripts': '*.py', 'docs/deployment': '*.md'}
DOC_SUFFIXES = {'.md', '.csv', '.html', '.yaml', '.json'}


def main():
    output = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / 'outputs/storysonic-lab-source.tar.gz').absolute()
    output.parent.mkdir(parents=True, exist_ok=True)
    paths = [ROOT / n for n in FILES]
    paths.extend(ROOT / n for n in ['scripts/setup-mac.sh', 'scripts/run-mac.sh'])
    for directory, pattern in DIRECTORIES.items():
        paths.extend((ROOT / directory).glob(pattern))
    tracked = subprocess.check_output(
        ['git', '-C', str(ROOT), 'ls-files', '--', 'docs/'], text=True
    ).splitlines()
    paths.extend(ROOT / p for p in tracked if Path(p).suffix in DOC_SUFFIXES)
    with tarfile.open(output, 'w:gz') as tar:
        for path in sorted(set(paths)):
            if path.is_symlink():
                raise ValueError(f'Package input must not be a symlink: {path.name}')
            if path.is_file() and path.suffix not in ('.mp3', '.m4a', '.wav', '.pyc'):
                tar.add(path, arcname=str(Path('storysonic-lab') / path.relative_to(ROOT)), recursive=False)
    print(output)


if __name__ == '__main__':
    main()
