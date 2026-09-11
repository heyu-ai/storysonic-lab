"""Optional ASR adapters, loaded only when transcription is requested."""

from contextlib import redirect_stdout
from importlib.metadata import version
from pathlib import Path
import platform
import sys

from .download import file_hashes
from .processing import fingerprint


DEFAULT_MODELS = {'mlx': 'mlx-community/whisper-large-v3-turbo',
                  'faster-whisper': 'Systran/faster-whisper-small'}


class Engine:
    def __init__(self, backend, *, model=None, model_dir=None, cache_dir=Path('data/models'), language='auto'):
        if backend not in DEFAULT_MODELS:
            raise ValueError('backend 必須為 mlx 或 faster-whisper')
        if backend == 'mlx' and (platform.system() != 'Darwin' or platform.machine() != 'arm64'):
            raise ValueError('MLX 需要 Apple Silicon macOS；Docker 請使用 --backend faster-whisper')
        if model_dir and model:
            raise ValueError('--model 與 --model-dir 不可同時指定')
        self.backend = backend
        self.language = None if language == 'auto' else language
        try:
            package = 'mlx-whisper' if backend == 'mlx' else 'faster-whisper'
            package_version = version(package)
            if backend == 'mlx':
                import mlx_whisper
                self.api = mlx_whisper
            else:
                import faster_whisper
                self.api = faster_whisper
            if model_dir:
                self.model_path = Path(model_dir).absolute()
            else:
                from huggingface_hub import snapshot_download
                self.model_path = Path(snapshot_download(
                    repo_id=model or DEFAULT_MODELS[backend], cache_dir=str(Path(cache_dir).absolute()),
                    allow_patterns=['*.json', '*.safetensors', '*.npz', '*.bin', '*.txt']))
        except ImportError as exc:
            extra = 'mac' if backend == 'mlx' else 'cpu'
            raise ValueError(f'缺少轉錄依賴；請安裝 storysonic-lab[{extra}] 或執行安裝腳本') from exc
        files = {}
        for path in sorted(self.model_path.iterdir()):
            if path.is_file() and path.suffix in ('.json', '.safetensors', '.npz', '.bin', '.txt'):
                files[path.name] = file_hashes(path)['sha256']
        if not files or not any(n.endswith(('.safetensors', '.npz', '.bin')) for n in files):
            raise ValueError('模型目錄沒有模型權重；請指定此 backend 的完整模型目錄')
        self.recipe = {'backend': backend, 'engine_version': package_version,
                       'model_sha256': fingerprint(files), 'model_files': files,
                       'language': language, 'task': 'transcribe', 'condition_on_previous_text': False,
                       'compute_type': 'float16' if backend == 'mlx' else 'int8',
                       'decoding': 'mlx-temperature-0' if backend == 'mlx' else 'beam-5-no-vad'}
        self.model = None

    def transcribe(self, audio):
        # Third-party progress belongs on stderr; stdout is the CLI event stream.
        with redirect_stdout(sys.stderr):
            if self.backend == 'mlx':
                return self.api.transcribe(str(audio), path_or_hf_repo=str(self.model_path),
                                           language=self.language, task='transcribe', verbose=False,
                                           condition_on_previous_text=False, temperature=0.0)
            if self.model is None:
                self.model = self.api.WhisperModel(str(self.model_path), device='cpu', compute_type='int8')
            segments, info = self.model.transcribe(str(audio), language=self.language, task='transcribe',
                                                  beam_size=5, condition_on_previous_text=False, vad_filter=False)
            return {'language': info.language,
                    'segments': [{'start': s.start, 'end': s.end, 'text': s.text} for s in segments]}
