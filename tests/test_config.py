import os
from pathlib import Path
import tempfile
import unittest

from llm_playing_minecraft.config import AppConfig, ConfigError


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.original_env = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_requires_api_key(self):
        os.environ.pop("MINECRAFT_LLM_API_KEY", None)
        os.environ.pop("LMSTUDIO_API_KEY", None)
        os.environ.pop("OPENAI_API_KEY", None)

        with self.assertRaises(ConfigError):
            AppConfig.from_env(env_file=None)

    def test_loads_env_file_defaults(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text(
                "\n".join(
                    [
                        "MINECRAFT_LLM_API_KEY=test-key",
                        "MINECRAFT_LLM_MODEL=google/gemma-4-e4b",
                    ]
                ),
                encoding="utf-8",
            )

            config = AppConfig.from_env(env_file=env_path)

        self.assertEqual(config.api_key, "test-key")
        self.assertEqual(config.model, "google/gemma-4-e4b")
        self.assertEqual(config.base_url, "http://localhost:1234/api/v1")
        self.assertEqual(config.context_length, 16384)
        self.assertEqual(config.baritone_profile, "bold")

    def test_rejects_tiny_context_length(self):
        os.environ["MINECRAFT_LLM_API_KEY"] = "test-key"
        os.environ["MINECRAFT_LLM_CONTEXT_LENGTH"] = "512"

        with self.assertRaises(ConfigError):
            AppConfig.from_env(env_file=None)


if __name__ == "__main__":
    unittest.main()
