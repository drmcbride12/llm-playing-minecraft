import unittest

from llm_playing_minecraft.prompts import SYSTEM_PROMPT, build_messages


class PromptTests(unittest.TestCase):
    def test_system_prompt_contains_json_schema(self):
        self.assertIn('"baritone_command"', SYSTEM_PROMPT)
        self.assertIn("#mine", SYSTEM_PROMPT)

    def test_build_messages_truncates_large_observation(self):
        messages = build_messages(
            "collect wood",
            "x" * 10000,
            context_length=1200,
            baritone_profile="bold",
        )

        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("truncated", messages[1]["content"])
        self.assertIn("bold", messages[1]["content"])


if __name__ == "__main__":
    unittest.main()
