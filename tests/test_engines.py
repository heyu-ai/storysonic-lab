import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from storysonic.engines import Engine


class EngineTests(unittest.TestCase):
    def test_mlx_parameters_and_model_fingerprint_survive_migration(self):
        with tempfile.TemporaryDirectory() as tmp:
            model = Path(tmp)
            (model / 'config.json').write_text('{}')
            (model / 'weights.safetensors').write_bytes(b'model')
            api = Mock()
            api.transcribe.return_value = {'language': 'en', 'segments': []}
            with patch.dict('sys.modules', {'mlx_whisper': api}), \
                    patch('storysonic.engines.platform.system', return_value='Darwin'), \
                    patch('storysonic.engines.platform.machine', return_value='arm64'), \
                    patch('storysonic.engines.version', return_value='test'):
                engine = Engine('mlx', model_dir=model)
                self.assertEqual(engine.transcribe(Path('test.mp3'))['language'], 'en')
            self.assertNotIn(str(model), json.dumps(engine.recipe))
            kwargs = api.transcribe.call_args.kwargs
            self.assertEqual(kwargs['task'], 'transcribe')
            self.assertIsNone(kwargs['language'])
            self.assertFalse(kwargs['condition_on_previous_text'])

    def test_faster_whisper_consumes_generator_and_uses_cpu(self):
        with tempfile.TemporaryDirectory() as tmp:
            model = Path(tmp)
            (model / 'model.bin').write_bytes(b'model')
            api = Mock()
            api.WhisperModel.return_value.transcribe.return_value = (
                iter([SimpleNamespace(start=0, end=1, text='hello')]), SimpleNamespace(language='en'))
            with patch.dict('sys.modules', {'faster_whisper': api}), patch('storysonic.engines.version', return_value='test'):
                engine = Engine('faster-whisper', model_dir=model)
                result = engine.transcribe(Path('test.m4a'))
            self.assertEqual(result['segments'], [{'start': 0, 'end': 1, 'text': 'hello'}])
            self.assertEqual(api.WhisperModel.call_args.kwargs['device'], 'cpu')
            self.assertEqual(api.WhisperModel.call_args.kwargs['compute_type'], 'int8')

    def test_mlx_on_linux_is_actionable(self):
        with patch('storysonic.engines.platform.system', return_value='Linux'):
            with self.assertRaisesRegex(ValueError, 'Apple Silicon'):
                Engine('mlx')
