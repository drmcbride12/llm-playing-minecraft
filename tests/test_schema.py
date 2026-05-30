import json
import unittest

from llm_playing_minecraft.schema import (
    ActionValidationError,
    AgentAction,
    parse_action_response,
    safe_fallback_action,
)


class AgentActionTests(unittest.TestCase):
    def test_accepts_safe_baritone_command(self):
        action = AgentAction.from_mapping(
            {
                "reason": "Need wood before crafting tools.",
                "baritone_command": "#mine oak_log",
                "wait_seconds": 3,
            }
        )

        self.assertEqual(action.baritone_command, "#mine oak_log")
        self.assertEqual(action.wait_seconds, 3)

    def test_rejects_slash_commands(self):
        with self.assertRaises(ActionValidationError):
            AgentAction.from_mapping(
                {
                    "reason": "This should not be allowed.",
                    "baritone_command": "/op player",
                }
            )

    def test_rejects_targetless_mine_command(self):
        with self.assertRaises(ActionValidationError):
            AgentAction.from_mapping(
                {
                    "reason": "Need a concrete block target.",
                    "baritone_command": "#mine",
                }
            )

    def test_extracts_json_from_code_fence(self):
        response = """```json
{"reason": "Scout for trees.", "baritone_command": "#explore", "wait_seconds": 1}
```"""

        action = parse_action_response(response)

        self.assertEqual(action.reason, "Scout for trees.")
        self.assertEqual(action.baritone_command, "#explore")

    def test_fallback_stops_baritone(self):
        action = safe_fallback_action(ValueError("bad model output"))

        self.assertEqual(action.baritone_command, "#stop")
        self.assertIn("bad model output", action.reason)

    def test_round_trip_render_shape(self):
        action = AgentAction(
            reason="Goal satisfied.",
            chat="Done.",
            baritone_command=None,
            wait_seconds=0,
            done=True,
        )

        payload = json.loads(json.dumps(action.to_dict()))

        self.assertTrue(payload["done"])
        self.assertEqual(payload["chat"], "Done.")


if __name__ == "__main__":
    unittest.main()
