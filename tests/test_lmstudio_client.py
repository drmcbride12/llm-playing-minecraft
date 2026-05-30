import unittest

from llm_playing_minecraft.lmstudio_client import extract_chat_content


class LMStudioClientTests(unittest.TestCase):
    def test_extracts_native_message_and_ignores_reasoning(self):
        payload = {
            "output": [
                {"type": "reasoning", "content": "Internal planning."},
                {"type": "message", "content": '{"ok": true}'},
            ]
        }

        self.assertEqual(extract_chat_content(payload), '{"ok": true}')

    def test_extracts_openai_compatible_message(self):
        payload = {
            "choices": [
                {
                    "message": {
                        "content": '{"ok": true}',
                    }
                }
            ]
        }

        self.assertEqual(extract_chat_content(payload), '{"ok": true}')


if __name__ == "__main__":
    unittest.main()
