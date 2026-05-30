import json
import unittest

from llm_playing_minecraft.observations import (
    compact_observation_from_text,
    summarize_block_cloud,
)


class ObservationTests(unittest.TestCase):
    def test_renders_compact_observation(self):
        text = compact_observation_from_text(
            json.dumps(
                {
                    "summary": "Trees nearby.",
                    "player": {"biome": "plains"},
                    "important_blocks": [
                        {"block": "oak_log", "nearest": "8m north", "count": 14}
                    ],
                }
            )
        )

        self.assertIn("Summary: Trees nearby.", text)
        self.assertIn("Player: biome=plains", text)
        self.assertIn("oak_log", text)

    def test_summarizes_raw_block_cloud(self):
        summary = summarize_block_cloud(
            [
                {"block": "oak_log", "pos": {"x": 1, "y": 64, "z": 2}},
                {"block": "oak_log", "pos": {"x": 2, "y": 64, "z": 2}},
                {"block": "stone", "pos": {"x": 3, "y": 63, "z": 2}},
            ]
        )

        self.assertEqual(summary[0]["block"], "oak_log")
        self.assertEqual(summary[0]["count"], 2)
        self.assertEqual(summary[0]["range"]["x"], [1, 2])


if __name__ == "__main__":
    unittest.main()
